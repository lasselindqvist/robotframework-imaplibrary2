IMAP email testing library for Robot Framework
==============================================

[Docs](https://lasselindqvist.github.io/robotframework-imaplibrary2/doc/ImapLibrary2.html)

Introduction
------------

Note: This is a fork of
<https://github.com/rickypc/robotframework-imaplibrary>

ImapLibrary2 is a IMAP email testing library for [Robot
Framework](http://goo.gl/lES6WM).

More information about this library can be found in the [Keyword
Documentation](https://lasselindqvist.github.io/robotframework-imaplibrary2/doc/ImapLibrary2.html).

If you are interested to contribute back to this project, please see
**Contributing** section.

### Examples

``` {.sourceCode .robotframework}
*** Settings ***
Library    ImapLibrary2

*** Test Cases ***
Email Verification
    Open Mailbox    host=imap.domain.com    user=email@domain.com    password=secret
    ${LATEST} =    Wait For Email    sender=noreply@domain.com    timeout=300
    ${HTML} =    Open Link From Email    ${LATEST}
    Should Contain    ${HTML}    Your email address has been updated
    Close Mailbox

Multipart Email Verification
    Open Mailbox    host=imap.domain.com    user=email@domain.com    password=secret
    ${LATEST} =    Wait For Email    sender=noreply@domain.com    timeout=300
    ${parts} =    Walk Multipart Email    ${LATEST}
    :FOR    ${i}    IN RANGE    ${parts}
    \\    Walk Multipart Email    ${LATEST}
    \\    ${content-type} =    Get Multipart Content Type
    \\    Continue For Loop If    '${content-type}' != 'text/html'
    \\    ${payload} =    Get Multipart Payload    decode=True
    \\    Should Contain    ${payload}    your email
    \\    ${HTML} =    Open Link From Email    ${LATEST}
    \\    Should Contain    ${HTML}    Your email
    Close Mailbox
```

Installation
------------

### Using `pip`

The recommended installation method is using
[pip](http://goo.gl/jlJCPE):

``` {.sourceCode .console}
pip install robotframework-imaplibrary2
```

The main benefit of using `pip` is that it automatically installs all
dependencies needed by the library. Other nice features are easy
upgrading and support for un-installation:

``` {.sourceCode .console}
pip install --upgrade robotframework-imaplibrary2
pip uninstall robotframework-imaplibrary2
```

Notice that using `--upgrade` above updates both the library and all its
dependencies to the latest version. If you want, you can also install a
specific version:

``` {.sourceCode .console}
pip install robotframework-imaplibrary2==x.x.x
```

### Proxy configuration

If you are behind a proxy, you can use `--proxy` command line option or
set `http_proxy` and/or `https_proxy` environment variables to configure
`pip` to use it. If you are behind an authenticating NTLM proxy, you may
want to consider installing [CNTML](http://goo.gl/ukiwSO) to handle
communicating with it.

For more information about `--proxy` option and using pip with proxies
in general see:

-   <http://pip-installer.org/en/latest/usage.html>
-   <http://stackoverflow.com/questions/9698557/how-to-use-pip-on-windows-behind-an-authenticating-proxy>
-   <http://stackoverflow.com/questions/14149422/using-pip-behind-a-proxy>

### Manual installation

If you do not have network connection or cannot make proxy to work, you
need to resort to manual installation. This requires installing both the
library and its dependencies yourself.

-   Make sure you have [Robot Framework
    installed](https://goo.gl/PFbWqM).
-   Download source distributions (`*.tar.gz`) for the library:
    -   <https://pypi.python.org/pypi/robotframework-imaplibrary2>
-   Download PGP signatures (`*.tar.gz.asc`) for signed packages.
-   Find each public key used to sign the package:

``` {.sourceCode .console}
gpg --keyserver pgp.mit.edu --search-keys D1406DE7
```

-   Select the number from the list to import the public key
-   Verify the package against its PGP signature:

``` {.sourceCode .console}
gpg --verify robotframework-imaplibrary2-x.x.x.tar.gz.asc robotframework-imaplibrary2-x.x.x.tar.gz
```

-   Extract each source distribution to a temporary location.
-   Go to each created directory from the command line and install each
    project using:

``` {.sourceCode .console}
python setup.py install
```

If you are on Windows, and there are Windows installers available for
certain projects, you can use them instead of source distributions. Just
download 32bit or 64bit installer depending on your system, double-click
it, and follow the instructions.

Directory Layout
----------------

doc/
:   [Keyword documentation](https://lasselindqvist.github.io/robotframework-imaplibrary2/doc/ImapLibrary2.html)

src/
:   Python source code

test/
:   Test files

    utest/
    :   Python unit test

Usage
-----

To write tests with Robot Framework and ImapLibrary, ImapLibrary must be
imported into your Robot test suite.

``` {.sourceCode .robotframework}
*** Settings ***
Library    ImapLibrary2
```

See [Robot Framework User Guide](http://goo.gl/Q7dfPB) for more
information.

More information about Robot Framework standard libraries and built-in
tools can be found in the [Robot Framework
Documentation](http://goo.gl/zy53tf).

Building Keyword Documentation
------------------------------

The [Keyword Documentation](https://lasselindqvist.github.io/robotframework-imaplibrary2/doc/ImapLibrary2.html) can be found online,
if you need to generate the keyword documentation, run:

``` {.sourceCode .console}
make doc
```
or

```
python -m robot.libdoc src/ImapLibrary2 doc/ImapLibrary2.html
```

Run Unit Tests, and Test Coverage Report
----------------------------------------

Test the testing library, talking about dogfooding, let's run:

``` {.sourceCode .console}
make test
```

Deploying to Pypi
------------

Delete old dist directory or empty it from old files.

``` {.sourceCode .console}
python setup.py sdist bdist_wheel
twine upload dist/*
```

If upload fails to HTTP 400 "Only one sdist may be uploaded per release.", delete the .zip file from dist directory and only upload the robotframework_imaplibrary2-x.x.xx.tar.gz

Contributing
------------

If you would like to contribute code to Imap Library project you can do
so through GitHub by forking the repository and sending a pull request.

When submitting code, please make every effort to follow existing
conventions and style in order to keep the code as readable as possible.
Please also include appropriate test cases.

That's it! Thank you for your contribution!

License
-------

Copyright (c) 2015-2016 Richard Huang.

This library is free software, licensed under: [Apache License, Version
2.0](https://goo.gl/qpvnnB).

Documentation and other similar content are provided under [Creative
Commons Attribution-NonCommercial-ShareAlike 4.0 International
License](http://goo.gl/SNw73V).
