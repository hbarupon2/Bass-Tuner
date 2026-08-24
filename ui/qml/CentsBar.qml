import QtQuick

Item {
    id: root
    property real cents: 0
    property bool centsValid: false
    property int span: 50
    property real inTuneCents: 5
    property string centsLabel: ""
    property string markFont: "Inter"
    property string centsFont: "Inter"
    property string heavyFont: "Inter"
    property string musicFont: "STIXGeneral"
    property color lime: "#3be85c"
    property real sy: 600 / 1024
    clip: false

    readonly property real lo: -span
    readonly property real hi: span
    readonly property var majorMarks: span <= 25
        ? [-25, -15, -5, 0, 5, 15, 25]
        : [-50, -30, -10, 0, 10, 30, 50]
    readonly property int markPx: Math.max(10, Math.round(22 * root.sy))
    readonly property int majorTickH: Math.max(4, Math.round(10 * root.sy))
    readonly property int zeroTickH: Math.max(6, Math.round(14 * root.sy))
    readonly property int needleNudgeY: 15

    function centsX(value) {
        const clamped = Math.max(lo, Math.min(hi, value))
        const t = (clamped - lo) / (hi - lo)
        const inset = bar.height / 2
        return bar.x + inset + t * (bar.width - 2 * inset)
    }

    function hexRgb(hex) {
        const h = hex.charAt(0) === "#" ? hex.substring(1) : hex
        return [
            parseInt(h.substring(0, 2), 16) / 255,
            parseInt(h.substring(2, 4), 16) / 255,
            parseInt(h.substring(4, 6), 16) / 255
        ]
    }

    function barColorAt(centsVal) {
        const t = (centsVal - lo) / Math.max(1, hi - lo)
        const stops = [
            [0.00, "#e4382a"],
            [0.10, "#ef3a1c"],
            [0.20, "#f07a12"],
            [0.28, "#f0b414"],
            [0.38, "#8ee24a"],
            [0.50, "#3bcf56"],
            [0.62, "#8ee24a"],
            [0.72, "#f0b414"],
            [0.80, "#f07a12"],
            [0.90, "#ef3a1c"],
            [1.00, "#e4382a"]
        ]
        let i = 0
        while (i < stops.length - 1 && t > stops[i + 1][0])
            i++
        const a = stops[i]
        const b = stops[Math.min(i + 1, stops.length - 1)]
        const spanT = b[0] - a[0]
        const u = spanT <= 0 ? 0 : (t - a[0]) / spanT
        const ca = hexRgb(a[1])
        const cb = hexRgb(b[1])
        return Qt.rgba(
            ca[0] + (cb[0] - ca[0]) * u,
            ca[1] + (cb[1] - ca[1]) * u,
            ca[2] + (cb[2] - ca[2]) * u,
            1
        )
    }

    Canvas {
        id: bar
        anchors.horizontalCenter: parent.horizontalCenter
        y: Math.round(parent.height * 0.46)
        width: Math.round(parent.width * 0.906)
        height: Math.max(16, Math.round(34 * root.sy))
        antialiasing: true
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d")
            const w = width
            const h = height
            const r = Math.max(2, Math.round(8 * root.sy))
            ctx.clearRect(0, 0, w, h)

            function roundRect(x, y, rw, rh, rad) {
                ctx.beginPath()
                ctx.moveTo(x + rad, y)
                ctx.lineTo(x + rw - rad, y)
                ctx.quadraticCurveTo(x + rw, y, x + rw, y + rad)
                ctx.lineTo(x + rw, y + rh - rad)
                ctx.quadraticCurveTo(x + rw, y + rh, x + rw - rad, y + rh)
                ctx.lineTo(x + rad, y + rh)
                ctx.quadraticCurveTo(x, y + rh, x, y + rh - rad)
                ctx.lineTo(x, y + rad)
                ctx.quadraticCurveTo(x, y, x + rad, y)
                ctx.closePath()
            }

            roundRect(0, 0, w, h, r)
            const g = ctx.createLinearGradient(0, 0, w, 0)
            g.addColorStop(0.00, "#4f1414")
            g.addColorStop(0.08, "#e2341b")
            g.addColorStop(0.18, "#f07a12")
            g.addColorStop(0.28, "#f0a80d")
            g.addColorStop(0.38, "#28591a")
            g.addColorStop(0.45, "#0a120c")
            g.addColorStop(0.50, "#070e0c")
            g.addColorStop(0.55, "#0a120c")
            g.addColorStop(0.62, "#194e1f")
            g.addColorStop(0.72, "#f0a80d")
            g.addColorStop(0.82, "#f07a12")
            g.addColorStop(0.92, "#e2341b")
            g.addColorStop(1.00, "#4e1316")
            ctx.fillStyle = g
            ctx.fill()

            ctx.save()
            roundRect(0, 0, w, h, r)
            ctx.clip()
            const rim = ctx.createLinearGradient(0, 0, w, 0)
            rim.addColorStop(0.00, "#e4382a")
            rim.addColorStop(0.12, "#ef3a1c")
            rim.addColorStop(0.22, "#f07a12")
            rim.addColorStop(0.32, "#f0b414")
            rim.addColorStop(0.42, "#52ed5e")
            rim.addColorStop(0.50, "#52ed5e")
            rim.addColorStop(0.58, "#52ed5e")
            rim.addColorStop(0.68, "#f0b414")
            rim.addColorStop(0.78, "#f07a12")
            rim.addColorStop(0.88, "#ef3a1c")
            rim.addColorStop(1.00, "#e4382a")
            ctx.fillStyle = rim
            ctx.fillRect(0, 0, w, 2)
            ctx.fillRect(0, h - 2, w, 2)
            ctx.restore()
        }
    }

    Repeater {
        model: Math.round((root.hi - root.lo) / 2) + 1
        Rectangle {
            required property int index
            readonly property int centsVal: root.lo + index * 2
            readonly property bool isZero: centsVal === 0
            readonly property bool major: root.majorMarks.indexOf(centsVal) >= 0
            width: isZero ? 2 : (major ? 1.6 : 1)
            height: isZero ? root.zeroTickH : (major ? root.majorTickH : Math.max(3, Math.round(5 * root.sy)))
            x: root.centsX(centsVal) - width / 2
            y: bar.y - height + 1
            color: root.barColorAt(centsVal)
            radius: 0.4
        }
    }

    Repeater {
        model: root.majorMarks
        Text {
            required property int modelData
            text: modelData === 0 ? "0" : (modelData > 0 ? "+" + modelData : "" + modelData)
            x: root.centsX(modelData) - width / 2
            y: bar.y - root.zeroTickH - Math.max(8, Math.round(14 * root.sy)) - height
            color: root.barColorAt(modelData)
            font.family: root.markFont
            font.pixelSize: root.markPx
            font.weight: Font.DemiBold
        }
    }

    Text {
        text: "IN TUNE"
        anchors.horizontalCenter: bar.horizontalCenter
        anchors.verticalCenter: bar.verticalCenter
        color: "#52ed5e"
        opacity: 1
        font.family: root.heavyFont
        font.pixelSize: Math.max(10, Math.round(20 * root.sy))
        font.letterSpacing: -0.6
        font.weight: Font.ExtraBold
    }

    Accidental {
        id: flatMark
        kind: "flat"
        ink: "#e4382a"
        fontFamily: root.musicFont
        x: bar.x
        y: bar.y + bar.height + Math.round(4 * root.sy)
        width: Math.max(22, Math.round(32 * root.sy))
        height: Math.max(32, Math.round(48 * root.sy))
    }

    Accidental {
        id: sharpMark
        kind: "sharp"
        ink: "#e4382a"
        fontFamily: root.musicFont
        x: bar.x + bar.width - width
        y: bar.y + bar.height + Math.round(4 * root.sy)
        width: Math.max(24, Math.round(34 * root.sy))
        height: Math.max(32, Math.round(48 * root.sy))
    }

    Text {
        id: centsReadout
        visible: root.centsValid
        z: 4
        text: root.centsLabel
        y: Math.round(20 * root.sy) - root.needleNudgeY
        height: font.pixelSize + 2
        verticalAlignment: Text.AlignBottom
        anchors.horizontalCenter: needle.horizontalCenter
        color: "#ffffff"
        font.family: root.heavyFont
        font.pixelSize: 22
        font.weight: Font.ExtraBold
        font.letterSpacing: -0.4
        lineHeightMode: Text.FixedHeight
        lineHeight: font.pixelSize
    }

    Item {
        id: needle
        visible: root.centsValid
        x: root.centsX(root.cents) - width / 2
        y: centsReadout.y + centsReadout.height + Math.round(3 * root.sy)
        width: 36
        height: bar.height + (bar.y - y) + 21 - root.needleNudgeY
        z: 3

        Canvas {
            anchors.fill: parent
            antialiasing: true
            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()
            onPaint: {
                const ctx = getContext("2d")
                const w = width
                const h = height
                const cx = w / 2
                ctx.clearRect(0, 0, w, h)
                ctx.shadowColor = "rgba(255,255,255,0.35)"
                ctx.shadowBlur = 4
                ctx.fillStyle = "#ffffff"
                ctx.strokeStyle = "#ffffff"
                ctx.lineCap = "round"
                ctx.lineJoin = "round"

                const tw = 16
                const th = 13
                const top = 2
                ctx.beginPath()
                ctx.moveTo(cx - tw / 2, top)
                ctx.lineTo(cx + tw / 2, top)
                ctx.lineTo(cx, top + th)
                ctx.closePath()
                ctx.fill()

                ctx.lineWidth = 6
                ctx.beginPath()
                ctx.moveTo(cx, top + th - 2)
                ctx.lineTo(cx, h - 3)
                ctx.stroke()
            }
        }
    }

}
