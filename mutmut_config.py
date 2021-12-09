import os.path

def pre_mutation(context):
    dirname, filename = os.path.split(context.filename)
    testfile = "test_" + filename
    context.config.test_command += ' ' + os.path.join("test", testfile)