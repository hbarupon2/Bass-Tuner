import QtQuick

Item {
    id: root
    property string label: ""
    property bool selected: false
    property bool chevron: false
    property string fontFamily: "Inter"
    property color lime: "#3be85c"
    signal tapped()

    implicitHeight: 32
    implicitWidth: Math.max(64, labelText.implicitWidth + (chevron ? 36 : 24))

    Repeater {
        model: root.selected ? 2 : 0
        Rectangle {
            required property int index
            anchors.centerIn: body
            width: body.width + 3 + index * 3
            height: body.height + 3 + index * 3
            radius: body.radius + 2 + index
            color: "transparent"
            border.width: 1.5
            border.color: root.lime
            opacity: 0.18 - index * 0.08
            z: 0
            enabled: false
        }
    }

    Rectangle {
        id: body
        anchors.fill: parent
        radius: 6
        color: root.selected ? "#333330" : "#2a2a28"
        border.width: root.selected ? 2.6 : 1
        border.color: root.selected ? "#3be85c" : "#1c1c1a"
        z: 1

        Text {
            id: labelText
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: root.chevron ? 22 : 10
            text: root.label
            color: "#ffffff"
            font.family: root.fontFamily
            font.pixelSize: Math.max(12, Math.round(root.height * 0.48))
            font.letterSpacing: -0.6
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            horizontalAlignment: Text.AlignHCenter
        }

        Canvas {
            visible: root.chevron
            z: 1
            width: 12
            height: 16
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 10
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "#d8d8d6"
                ctx.lineWidth = 2
                ctx.lineCap = "round"
                ctx.lineJoin = "round"
                ctx.beginPath()
                ctx.moveTo(3, 3)
                ctx.lineTo(9, height / 2)
                ctx.lineTo(3, height - 3)
                ctx.stroke()
            }
        }
    }

    MouseArea {
        anchors.fill: parent
        z: 2
        onClicked: root.tapped()
    }
}
