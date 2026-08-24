import QtQuick

Item {
    id: root
    property string fontFamily: "Inter"
    property real from: 0
    property real to: 1
    property real value: 0
    property string valueText: ""
    property string loLabel: ""
    property string hiLabel: ""
    signal moved(real value)

    implicitHeight: 36

    Rectangle {
        id: track
        anchors.left: parent.left
        anchors.right: valueLabel.left
        anchors.rightMargin: 10
        anchors.verticalCenter: parent.verticalCenter
        height: 2
        color: "#484848"
    }

    Text {
        text: root.loLabel
        anchors.left: track.left
        anchors.top: track.bottom
        anchors.topMargin: 4
        color: "#b0b0b0"
        font.family: root.fontFamily
        font.pixelSize: 12
    }

    Text {
        text: root.hiLabel
        anchors.right: track.right
        anchors.top: track.bottom
        anchors.topMargin: 4
        color: "#b0b0b0"
        font.family: root.fontFamily
        font.pixelSize: 12
    }

    Rectangle {
        id: thumb
        width: 14
        height: 14
        radius: 7
        color: "#2ee164"
        y: track.y - 6
        x: track.x + (track.width - width) * Math.max(0, Math.min(1, (root.value - root.from) / (root.to - root.from)))
    }

    Text {
        id: valueLabel
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: 56
        horizontalAlignment: Text.AlignRight
        text: root.valueText
        color: "#ffffff"
        font.family: root.fontFamily
        font.pixelSize: 16
    }

    MouseArea {
        anchors.fill: track
        anchors.topMargin: -16
        anchors.bottomMargin: -16
        onPressed: root._emit(mouseX)
        onPositionChanged: if (pressed) root._emit(mouseX)
    }

    function _emit(mx) {
        const t = Math.max(0, Math.min(1, mx / track.width))
        root.moved(root.from + t * (root.to - root.from))
    }
}
