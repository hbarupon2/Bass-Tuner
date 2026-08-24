import QtQuick

Text {
    id: root
    property string kind: ""
    property color ink: "#ffffff"
    property string fontFamily: "STIXGeneral"

    visible: kind === "flat" || kind === "sharp"
    text: kind === "flat" ? "♭" : (kind === "sharp" ? "♯" : "")
    color: ink
    font.family: root.fontFamily
    font.pixelSize: Math.round(height * 0.92)
    verticalAlignment: Text.AlignVCenter
    horizontalAlignment: Text.AlignHCenter
}
