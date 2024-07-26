class RepositoryException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class CommitException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class AddException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class BranchException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class CheckoutException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class CherryPickException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message