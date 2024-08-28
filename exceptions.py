class RepositoryException(Exception):
    message: str


class CommitException(Exception):
    message: str


class AddException(Exception):
    message: str


class BranchException(Exception):
    message: str


class CheckoutException(Exception):
    message: str


class CherryPickException(Exception):
    message: str
