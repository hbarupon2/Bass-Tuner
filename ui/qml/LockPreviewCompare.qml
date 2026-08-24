import QtQuick

// Side-by-side: emoji reference vs app lock icon (for render_lock_preview.py).
Item {
    id: root
    property bool locked: false
    width: 160
    height: 48

    onLockedChanged: icon.requestPaint()

    Row {
        anchors.centerIn: parent
        spacing: 16
        Column {
            spacing: 2
            Text {
                text: root.locked ? "🔒" : "🔓"
                font.pixelSize: 28
                horizontalAlignment: Text.AlignHCenter
                width: 48
            }
            Text {
                text: "emoji"
                color: "#666"
                font.pixelSize: 9
                horizontalAlignment: Text.AlignHCenter
                width: 48
            }
        }
        Column {
            spacing: 2
            Canvas {
                id: icon
                width: 28
                height: 28
                onPaint: {
                    const ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    const scale = width / 24
                    ctx.save()
                    ctx.scale(scale, scale)
                    ctx.strokeStyle = root.locked ? "#3be85c" : "#f0880e"
                    ctx.lineWidth = 2.2
                    ctx.lineCap = "round"
                    ctx.lineJoin = "round"
                    function strokeRoundRect(x, y, rw, rh, r) {
                        ctx.beginPath()
                        ctx.moveTo(x + r, y)
                        ctx.lineTo(x + rw - r, y)
                        ctx.quadraticCurveTo(x + rw, y, x + rw, y + r)
                        ctx.lineTo(x + rw, y + rh - r)
                        ctx.quadraticCurveTo(x + rw, y + rh, x + rw - r, y + rh)
                        ctx.lineTo(x + r, y + rh)
                        ctx.quadraticCurveTo(x, y + rh, x, y + rh - r)
                        ctx.lineTo(x, y + r)
                        ctx.quadraticCurveTo(x, y, x + r, y)
                        ctx.closePath()
                        ctx.stroke()
                    }
                    strokeRoundRect(3, 11, 18, 11, 2)
                    ctx.beginPath()
                    if (root.locked) {
                        ctx.moveTo(7, 11)
                        ctx.lineTo(7, 7)
                        ctx.arc(12, 7, 5, Math.PI, 0, false)
                        ctx.lineTo(17, 11)
                    } else {
                        ctx.moveTo(7, 10)
                        ctx.lineTo(7, 7)
                        ctx.arc(12, 7, 5, Math.PI, Math.atan2(-1, 4.9), false)
                    }
                    ctx.stroke()
                    ctx.restore()
                }
                Component.onCompleted: requestPaint()
            }
            Text {
                text: "app"
                color: "#666"
                font.pixelSize: 9
                horizontalAlignment: Text.AlignHCenter
                width: 48
            }
        }
    }
}
