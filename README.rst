ftw.publisher.controlling
=========================

This package is an `ftw.publisher`_ addon, providing views for comparing
the state of the editorial and the public site, show inconsistent objects.

It is designed for use in a workflow based publisher environment.


Usage
-----

- Add ``ftw.publisher.controlling`` to your buildout configuration on
  the **editoral site** and run ``bin/buildout``:

::

    [instance]
    eggs +=
        ftw.publisher.sender
        ftw.publisher.controlling

- Configure the report in the publisher control panel.



Links
-----

- github project repository: https://github.com/4teamwork/ftw.publisher.controlling
- Main publisher github project repository: https://github.com/4teamwork/ftw.publisher.sender
- Issues: https://github.com/4teamwork/ftw.publisher.controlling/issues
- Pypi: http://pypi.python.org/pypi/ftw.publisher.controlling
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.publisher.controlling


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.publisher.controlling`` is licensed under GNU General Public License, version 2.


.. _ftw.publisher: https://github.com/4teamwork/ftw.publisher.sender
