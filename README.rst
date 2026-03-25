doujinshi-dl-nhentai
====================

nhentai plugin for `doujinshi-dl <https://github.com/RicterZ/doujinshi-dl>`_.

============
Installation
============

.. code-block::

   pip install doujinshi-dl
   pip install doujinshi-dl-nhentai

=====
Usage
=====

Set the mirror URL and run:

.. code-block:: bash

   export DOUJINSHI_DL_URL=https://nhentai.net
   doujinshi-dl --id 123456

Or inline:

.. code-block:: bash

   DOUJINSHI_DL_URL=https://nhentai.net doujinshi-dl --search "keyword" --download

The plugin is auto-discovered by the main package via the ``doujinshi_dl.plugins`` entry point — no extra configuration needed beyond installation.

===========
Development
===========

.. code-block:: bash

   pip install -e /path/to/doujinshi-dl
   pip install -e /path/to/doujinshi-dl-nhentai

=======
Testing
=======

.. code-block:: bash

   export DDL_COOKIE="<cookie>"
   export DDL_UA="<user-agent>"
   export DOUJINSHI_DL_URL="<mirror-url>"

   python -m unittest discover tests/

.. |license| image:: https://img.shields.io/github/license/ricterz/doujinshi-dl.svg
   :target: https://github.com/RicterZ/doujinshi-dl/blob/master/LICENSE
