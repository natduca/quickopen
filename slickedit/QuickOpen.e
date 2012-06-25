#include "slick.sh"
//
// NB - you will need to manually replace "/path/to/quickopen" to
// a path that is valid on your machine.
//
definit()
{
  // FIXME: find out how to run quickopend in the background without the wrapper.
  _str cmd = "/bin/sh /path/to/quickopen/slickedit/start_quickopend.sh";
  shell(cmd);
}
_command QuickOpen() name_info(','VSARG2_MACRO|VSARG2_MARK|VSARG2_REQUIRES_MDI_EDITORCTL)
{
  // Run quickopen.
  _str cmd = "/path/to/quickopen/quickopen search";
  _str filename = _PipeShellResult(cmd, 0, '');

  // Strip off the line feed characters that _PipeShellResult tacks on.
  filename = substr(filename, 1, length(filename)-2);

  // Open the file or warn the user.
  if (length(filename) > 0) {
    edit(filename);
  } else {
    message("No file selected");
  }
}
