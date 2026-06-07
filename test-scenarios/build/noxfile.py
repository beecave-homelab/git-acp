import nox


@nox.session(python=["3.11", "3.12"])
def tests(session: nox.Session) -> None:
    session.install("pytest")
    session.run("pytest", "-q")
