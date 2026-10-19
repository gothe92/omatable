import Quickshell
import QtQuick

// Omatable is a standalone window, not a shell surface. This overlay is only
// loaded when summoned, starts a new Omatable window, and dismisses itself, so
// nothing from the plugin stays running in the background.
//
//   omarchy-shell shell summon andras.omatable
//   omarchy-shell shell summon andras.omatable '{"path": "/path/to/file.sqlite"}'
Item {
  id: root

  property var shell: null
  property var manifest: null

  readonly property string appPath: decodeURIComponent(Qt.resolvedUrl("omatable").toString().replace(/^file:\/\//, ""))

  function open(payloadJson) {
    var payload = ({})
    try { payload = JSON.parse(payloadJson || "{}") } catch (e) { payload = ({}) }

    var command = ["setsid", "uwsm-app", "--", "python3", root.appPath]
    if (payload.path) command.push(String(payload.path))
    else if (payload.container) command.push(String(payload.container))
    Quickshell.execDetached(command)

    Qt.callLater(root.dismiss)
  }

  function close() {}

  function dismiss() {
    if (root.shell && typeof root.shell.hide === "function")
      root.shell.hide((root.manifest && root.manifest.id) || "andras.omatable")
  }
}
