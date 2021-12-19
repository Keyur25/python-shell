import os.path


def pre_mutation(context):
    filename = os.path.split(context.filename)[1]
    testfile = "test_" + filename
    context.config.test_command += " " + os.path.join("test", testfile)
