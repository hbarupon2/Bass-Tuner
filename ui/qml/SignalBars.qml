import QtQuick

Row {
    id: root
    property int filled: 0
    property int bars: 5
    property color lime: "#3be85c"
    property int barHeight: 16
    spacing: Math.max(2, Math.round(barHeight * 0.22))
    height: barHeight
    width: bars * barW + (bars - 1) * spacing

    readonly property int barW: Math.max(3, Math.round(barHeight * 0.28))

    Repeater {
        model: root.bars
        Rectangle {
            required property int index
            width: root.barW
            height: Math.max(3, Math.round(root.barHeight * (0.52 + index * 0.12)))
            radius: 1
            color: index < root.filled ? root.lime : "#3a3a38"
            anchors.bottom: parent.bottom
        }
    }
}
