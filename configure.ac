AC_INIT(plugins,1.0)
AM_INIT_AUTOMAKE(plugins,1.0)

AC_PATH_PROG(MSGFMT, msgfmt, AC_MSG_ERROR(Could not find msgfmt))

AM_PATH_PYTHON
AC_PYTHON_DEVEL

AC_PROG_CXX

CPPFLAGS="$CPPFLAGS $PYTHON_CPPFLAGS"
LDFLAGS="$LDFLAGS $PYTHON_LDFLAGS"

AC_ARG_WITH(po,
        AS_HELP_STRING([--with-po],[enable updating of po files]),
        [with_po="$withval"],[with_po="no"])
if test "$with_po" = "yes"; then
        AC_PATH_PROG(MSGINIT, msginit)
        AC_PATH_PROG(MSGMERGE, msgmerge)
        AC_PATH_PROG(MSGUNIQ, msguniq)
        AC_PATH_PROG(XGETTEXT, xgettext)
        if test -z "$MSGINIT" -o -z "$MSGMERGE" -o -z "$MSGUNIQ" -o -z "$XGETTEXT"; then
                AC_MSG_ERROR([Could not find required gettext tools])
        fi
fi
AM_CONDITIONAL(UPDATE_PO, test "$with_po" = "yes")

AC_ARG_WITH(arch,
	[  --with-arch=NAME box arch [[none,ah4,mipsel...]]],
	[ARCH="$withval"],[ARCH="mipsel"])
AC_SUBST(ARCH)
AC_DEFINE_UNQUOTED(ARCH,"$ARCH",[box arch])

AM_CONDITIONAL(SH4, test `echo "$ARCH" | cut -b 1-3` == "sh4")
AM_CONDITIONAL(MIPSEL, test `echo "$ARCH" | cut -b 1-6` == "mipsel")
AM_CONDITIONAL(ARM, test `echo "$ARCH" | cut -b 1-3` == "arm")

AC_OUTPUT([
Makefile
po/Makefile
src/Makefile
src/ubi_reader/Makefile
src/ubi_reader/ubi/Makefile
src/ubi_reader/ubi/block/Makefile
src/ubi_reader/ubi/headers/Makefile
src/ubi_reader/ubi/volume/Makefile
src/ubi_reader/ubi_io/Makefile
src/ubi_reader/ubifs/Makefile
src/ubi_reader/ubifs/nodes/Makefile
src/ubi_reader/ui/Makefile
src/elftools/construct/Makefile
src/elftools/construct/lib/Makefile
src/elftools/ehabi/Makefile
src/elftools/Makefile
src/elftools/common/Makefile
src/elftools/elf/Makefile
src/elftools/dwarf/Makefile
])
