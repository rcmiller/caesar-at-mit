from review.models import Submission, File, Chunk, Batch, Comment
from django.contrib.auth.models import User
from xml.dom.minidom import parseString
from subprocess import Popen, PIPE
from collections import defaultdict, Counter
import re, sys

checkstyle_settings = {
    'settings': '/var/django/caesar/preprocessor/checks.xml',
    'jar': '/var/django/caesar/preprocessor/checkstyle.jar',
    }

def generate_checkstyle_comments(code_objects, save, batch, suppress_comment_regexes):
  checkstyle_user,created = User.objects.get_or_create(username='checkstyle')

  module_histogram = Counter() # checkstyle module name => # of complaints it made
  message_example = {} # module name => example of a complaint

  for (submission, files, chunks) in code_objects:
    chunkMap = dict([(chunk.file.path, chunk) for chunk in chunks if chunk.student_lines > 0])
    print("%s: %s changed chunks for this submission." % (submission, len(chunkMap)))

    if len(chunkMap) == 0:
      continue

    sys.stdout.flush()
    sys.stderr.flush()
    commandLine = [
      'java',
      '-jar', checkstyle_settings['jar'],
      '-c', checkstyle_settings['settings'],
      '-f', 'xml'
      ] + list(chunkMap.keys())
    proc = Popen(commandLine, stdout=PIPE)
    xml = proc.communicate()[0]
    try:
      dom = parseString(xml)
    except:
      print(sys.exc_info()[0])
      continue

    for fileNode in dom.getElementsByTagName('file'):
      chunk = chunkMap[fileNode.getAttribute('name')]
      commentNodes = fileNode.getElementsByTagName('error') + fileNode.getElementsByTagName('warning')
      for commentNode in commentNodes:
        message = commentNode.getAttribute('message')
        line = commentNode.getAttribute('line')
        checkstyleModule = commentNode.getAttribute('source')
        module_histogram[checkstyleModule] += 1
        message_example[checkstyleModule] = message
        comment = Comment(
          type='S',
          text=message,
          chunk=chunk,
          batch=batch,
          author=checkstyle_user,
          start=line,
          end=line)
        if save:
          comment.save()
      print("checkstyle: on", chunk.name, 'I made', len(commentNodes), 'comments')
  
  print("overall checkstyle message frequencies:")
  for module, count in module_histogram.most_common():
    print(count, module.split('.')[-1], "e.g.", message_example[module])
