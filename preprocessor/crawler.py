import os, fnmatch, sys
from collections import defaultdict

def crawl_submissions(base_dir, includes, excludes):
  '''Crawls the students code and returns a dictionary mapping student usernames to
  absolute file paths of their code. NOTE: Does not guarantee that the users exist
  on the server.
  Params:
    base_dir: directory that contains all of the student sub-directories
    includes: list of filename patterns (using fnmatch syntax) that should be uploaded to Caesar.
               For example, '*.java' would match both Foo.java and src/foo/Bar.java.
    excludes: list of filename patterns that should be excluded from the upload
  Returns:
    Dictionary mapping user names (i.e. directories) to a list of pathnames, all of which start with base_dir.
  '''
  student_dirs = os.listdir(base_dir)
  student_code = defaultdict(list)
  unexpected_files = []

  def matchesAnyPattern(filename, patterns):
    return reduce(lambda p1,p2: p1 or p2, [fnmatch.fnmatch(filename, pattern) for pattern in patterns], False)

  for student_dir in student_dirs:
    filepath = base_dir + '/' + student_dir
    # Make sure we only take non-hidden directories
    if (not os.path.isdir(filepath)) or student_dir[0] == '.':
      continue
    all_files_for_this_student = []
    for root, _, files in os.walk(filepath):
      all_files_for_this_student.extend([root + '/' + file_path for file_path in files])
    for filename in all_files_for_this_student:
      if matchesAnyPattern(filename, excludes):
        continue
      elif matchesAnyPattern(filename, includes):
        student_code[student_dir].append(filename)
      else:
        unexpected_files.append(filename)

  if len(unexpected_files) > 0:
    print("""
unexpected files found:
    {unexpected_files}

To include these files in Caesar, update the included file patterns of the SubmitMilestone
and rerun the preprocessor.  The second run of the preprocessor will not reload all submissions,
only the ones that changed as a result of the updated file pattern.
    """.format(unexpected_files="\n    ".join(unexpected_files)), file=sys.stderr)

  return student_code
