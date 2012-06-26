#include "slick.sh"
_command QuickOpen() name_info(','VSARG2_MACRO|VSARG2_MARK|VSARG2_REQUIRES_MDI_EDITORCTL)
{
  // Run quickopen.
  _str filename = _PipeShellResult("quickopen", 0, '');

  // Strip off the line feed characters that _PipeShellResult tacks on.
  filename = substr(filename, 1, length(filename)-2);

  // Open the file or warn the user.
  if (length(filename) > 0) {
    edit(filename);
  } else {
    message("No file selected");
  }
}
