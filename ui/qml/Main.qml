import QtQuick
import QtQuick.Window

Window {
    id: win
    visible: true
    width: 1024
    height: 600
    minimumWidth: 1024
    minimumHeight: 600
    maximumWidth: 1024
    maximumHeight: 600
    title: "Bass Tuner"
    color: "#0e0e0e"
    flags: Qt.Window | Qt.FramelessWindowHint

    FontLoader { id: fontMedium; source: backend.fontUrl("Inter-Medium.ttf") }
    FontLoader { id: fontSemi; source: backend.fontUrl("Inter-SemiBold.ttf") }
    FontLoader { id: fontBold; source: backend.fontUrl("Inter-Bold.ttf") }
    FontLoader { id: fontHeavy; source: backend.fontUrl("Inter-ExtraBold.ttf") }
    FontLoader { id: fontNote; source: backend.fontUrl("InterDisplay-ExtraBold.ttf") }
    FontLoader { id: fontMusic; source: backend.fontUrl("STIXGeneral.otf") }

    TunerView {
        anchors.fill: parent
        visible: !backend.showSettings
        enabled: visible
        fontMedium: fontMedium.name
        fontSemi: fontSemi.name
        fontBold: fontBold.name
        fontHeavy: fontHeavy.name
        fontNote: fontNote.name
        fontChip: fontMedium.name
        fontMusic: fontMusic.name
    }

    SettingsView {
        anchors.fill: parent
        visible: backend.showSettings
        enabled: visible
        fontMedium: fontMedium.name
        fontSemi: fontSemi.name
        fontChip: fontMedium.name
    }

    Shortcut { sequence: "Escape"; onActivated: backend.showSettings ? backend.closeSettings() : Qt.quit() }
    Shortcut { sequence: "1"; onActivated: backend.selectString(1) }
    Shortcut { sequence: "2"; onActivated: backend.selectString(2) }
    Shortcut { sequence: "3"; onActivated: backend.selectString(3) }
    Shortcut { sequence: "4"; onActivated: backend.selectString(4) }
    Shortcut { sequence: "5"; onActivated: backend.selectString(5) }
    Shortcut { sequence: "6"; onActivated: backend.selectString(6) }
    Shortcut { sequence: "0"; onActivated: backend.autoString() }
    Shortcut { sequence: ","; onActivated: backend.cyclePreset(-1) }
    Shortcut { sequence: "."; onActivated: backend.cyclePreset(1) }
    Shortcut { sequence: "Left"; onActivated: backend.cyclePreset(-1) }
    Shortcut { sequence: "Right"; onActivated: backend.cyclePreset(1) }
}
