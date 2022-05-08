import asyncio
import functools
import logging
import os
import shutil

import aiofiles
from aiocache import cached
from jinja2 import Template

logger = logging.getLogger("easy_api.files")

__all__ = ["read_file", "copytree_and_render"]


@cached()
async def read_file(path):
    """ read file with cache """
    async with aiofiles.open(path) as f:
        content = await f.read()
    return content


# async def write_file(path, content):
#     """ write file """
#     async with aiofiles.open(path, 'w') as f:
#         await f.write(content)


def _copyfile(context: dict, src: str, dst: str, *, follow_symlinks=True):
    """ copy file from src to dst, and render sql_template with .jinja file extension """
    if src.endswith(".jinja"):
        origin_dst, _ = os.path.splitext(dst)
        # file name support jinja grammar
        if '{{' in origin_dst:
            origin_dst = Template(origin_dst).render(**context)
        with open(src, "r") as out_fp:
            with open(origin_dst, "w") as in_fp:
                # render sql_template from src to dst
                dst_content = Template(out_fp.read(), trim_blocks=True, lstrip_blocks=True).render(context)
                in_fp.write(dst_content)
        logger.debug("copy file: %s -> %s", src, origin_dst)
        return

    logger.debug("copy file: %s -> %s", src, dst)
    return shutil.copy2(src, dst, follow_symlinks=follow_symlinks)


def _copytree(src, dst, symlinks=False, ignore=None, copy_function=shutil.copy2,
              ignore_dangling_symlinks=False):
    """ copy source from shutil.copytree """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)

    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if symlinks:
                    # We can't just leave it to `copy_function` because legacy
                    # code with a custom `copy_function` may rely on copytree
                    # doing the right thing.
                    os.symlink(linkto, dstname)
                    shutil.copystat(srcname, dstname, follow_symlinks=not symlinks)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occurs. copy2 will raise an error
                    if os.path.isdir(srcname):
                        _copytree(srcname, dstname, symlinks, ignore,
                                  copy_function)
                    else:
                        copy_function(srcname, dstname)
            elif os.path.isdir(srcname):
                _copytree(srcname, dstname, symlinks, ignore, copy_function)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        # Copying file access times may fail on Windows
        if getattr(why, 'winerror', None) is None:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error(errors)
    return dst


async def copytree_and_render(src, dst, context):
    """ copytree and render sql_template to origin type file
        support file name container jinja grammar
    """
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None,
                               _copytree,
                               src, dst, False, None,
                               functools.partial(_copyfile, context))
