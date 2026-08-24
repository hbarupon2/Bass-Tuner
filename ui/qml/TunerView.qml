import QtQuick

Item {
    id: root
    property string fontMedium: "Inter"
    property string fontSemi: "Inter"
    property string fontBold: "Inter"
    property string fontHeavy: "Inter"
    property string fontNote: "Inter"
    property string fontChip: "Inter"
    property string fontMusic: "STIXGeneral"

    readonly property real sx: width / 1536
    readonly property real sy: height / 1024
    readonly property int pad: Math.round(57 * sx)
    readonly property int headerH: Math.round(88 * sy)
    readonly property int noteH: Math.round(342 * sy)
    readonly property int centsH: Math.round(190 * sy)
    readonly property int stringH: Math.round(200 * sy)
    readonly property int chipH: Math.round(100 * sy)
    readonly property color lime: "#3be85c"
    readonly property color silver: "#b0b0ae"
    readonly property int statusH: Math.max(0, height - headerH - noteH - centsH - stringH - chipH)

    Canvas {
        id: backdrop
        anchors.fill: parent
        z: 0
        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
        onPaint: {
            const ctx = getContext("2d")
            const w = width
            const h = height
            ctx.clearRect(0, 0, w, h)

            const bands = [
                { h: root.headerH, fill: "#0a0a0a", line: "#101010" },
                { h: root.noteH, fill: "#0f0f0f", line: "#101010" },
                { h: root.centsH, fill: "#0f0f0f", line: "#101110" },
                { h: root.stringH, fill: "#101110", line: "#141413" },
                { h: root.chipH, fill: "#141313", line: "#111111" },
                { h: root.statusH, fill: "#0c0c0c", line: null }
            ]

            let y = 0
            for (let i = 0; i < bands.length; i++) {
                const band = bands[i]
                const bh = Math.max(0, band.h)
                if (bh <= 0)
                    continue
                ctx.fillStyle = band.fill
                ctx.fillRect(0, y, w, bh)
                y += bh
                if (band.line && i < bands.length - 1) {
                    ctx.fillStyle = band.line
                    ctx.fillRect(0, y - 1, w, 1)
                }
            }
            if (y < h) {
                ctx.fillStyle = "#0c0c0c"
                ctx.fillRect(0, y, w, h - y)
            }

            let s = 246353
            function rnd() {
                s = (s * 1103515245 + 12345) & 0x7fffffff
                return s / 0x7fffffff
            }
            const n = Math.floor(w * h * 0.006)
            for (let i = 0; i < n; i++) {
                const x = rnd() * w
                const yy = rnd() * h
                const a = (0.012 + rnd() * 0.016).toFixed(3)
                ctx.fillStyle = rnd() > 0.5 ? ("rgba(255,255,255," + a + ")") : ("rgba(0,0,0," + a + ")")
                ctx.fillRect(x, yy, 1, 1)
            }
        }
    }

    Column {
        anchors.fill: parent
        spacing: 0
        z: 1

        Item {
            width: parent.width
            height: root.headerH

            Text {
                text: "BASS TUNER"
                color: root.silver
                font.family: root.fontMedium
                font.pixelSize: Math.round(32 * root.sy)
                font.letterSpacing: -0.7
                font.weight: Font.Medium
                anchors.left: parent.left
                anchors.leftMargin: root.pad
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: backend.presetTitle
                color: "#ffffff"
                font.family: root.fontBold
                font.pixelSize: Math.round(56 * root.sy)
                font.weight: Font.Bold
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
            }

            Item {
                width: 44
                height: 44
                anchors.right: parent.right
                anchors.rightMargin: root.pad - 8
                anchors.verticalCenter: parent.verticalCenter

                Canvas {
                    id: cog
                    width: 30
                    height: 30
                    anchors.centerIn: parent
                    antialiasing: true
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    onPaint: {
                        const ctx = getContext("2d")
                        const w = width
                        const h = height
                        const cx = w / 2
                        const cy = h / 2
                        const teeth = 8
                        const ro = w * 0.48
                        const ri = w * 0.33
                        const hole = w * 0.155
                        ctx.clearRect(0, 0, w, h)
                        ctx.fillStyle = "#c4c4c2"
                        ctx.beginPath()
                        for (let i = 0; i < teeth; i++) {
                            const a = (i / teeth) * Math.PI * 2 - Math.PI / 2
                            const step = Math.PI * 2 / teeth
                            const t0 = a - step * 0.18
                            const t1 = a + step * 0.18
                            const v0 = a + step * 0.32
                            const v1 = a + step * 0.68
                            if (i === 0)
                                ctx.moveTo(cx + ro * Math.cos(t0), cy + ro * Math.sin(t0))
                            else
                                ctx.lineTo(cx + ro * Math.cos(t0), cy + ro * Math.sin(t0))
                            ctx.lineTo(cx + ro * Math.cos(t1), cy + ro * Math.sin(t1))
                            ctx.lineTo(cx + ri * Math.cos(v0), cy + ri * Math.sin(v0))
                            ctx.lineTo(cx + ri * Math.cos(v1), cy + ri * Math.sin(v1))
                        }
                        ctx.closePath()
                        ctx.fill()
                        ctx.globalCompositeOperation = "destination-out"
                        ctx.beginPath()
                        ctx.arc(cx, cy, hole, 0, Math.PI * 2)
                        ctx.fill()
                        ctx.globalCompositeOperation = "source-over"
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: backend.openSettings()
                }
            }
        }

        Item {
            width: parent.width
            height: root.noteH

            Item {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: Math.round(-10 * root.sy)
                width: noteGlyph.width + (backend.noteAccidental === "" ? 0 : accGlyph.width + Math.round(8 * root.sx))
                height: noteGlyph.height

                Text {
                    id: noteGlyph
                    text: backend.noteLetter
                    color: backend.locked ? "#ffffff" : "#b0b0b0"
                    font.family: root.fontNote
                    font.pixelSize: Math.round(270 * root.sy)
                    font.weight: Font.ExtraBold
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                }

                Accidental {
                    id: accGlyph
                    kind: backend.noteAccidental
                    ink: noteGlyph.color
                    fontFamily: root.fontMusic
                    width: Math.round(72 * root.sx)
                    height: Math.round(180 * root.sy)
                    anchors.left: noteGlyph.right
                    anchors.leftMargin: Math.round(4 * root.sx)
                    anchors.verticalCenter: noteGlyph.verticalCenter
                    anchors.verticalCenterOffset: Math.round(18 * root.sy)
                }
            }

            Text {
                id: subtitleRow
                visible: backend.noteLetter === "—"
                text: backend.subtitle
                color: "#fbfbfb"
                font.family: root.fontMedium
                font.pixelSize: Math.round(46 * root.sy)
                font.letterSpacing: 0.2
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: Math.round(8 * root.sy)
            }

            Row {
                visible: backend.noteLetter !== "—"
                spacing: backend.noteAccidental === "" ? 0 : Math.round(4 * root.sx)
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.bottom: parent.bottom
                anchors.bottomMargin: Math.round(8 * root.sy)

                Text {
                    text: backend.noteLetter
                    color: "#fbfbfb"
                    font.family: root.fontMedium
                    font.pixelSize: Math.round(46 * root.sy)
                    font.letterSpacing: 0.2
                }

                Accidental {
                    kind: backend.noteAccidental
                    ink: "#fbfbfb"
                    fontFamily: root.fontMusic
                    width: Math.round(16 * root.sx)
                    height: Math.round(28 * root.sy)
                    anchors.verticalCenter: parent.verticalCenter
                }

                Text {
                    text: backend.subtitle
                    color: "#fbfbfb"
                    font.family: root.fontMedium
                    font.pixelSize: Math.round(46 * root.sy)
                    font.letterSpacing: 0.2
                }
            }
        }

        CentsBar {
            width: parent.width
            height: root.centsH
            cents: backend.cents
            centsValid: backend.centsValid
            span: backend.centsRange
            inTuneCents: backend.inTuneCents
            centsLabel: backend.centsLabel
            markFont: root.fontMedium
            centsFont: root.fontBold
            heavyFont: root.fontHeavy
            musicFont: root.fontMusic
            lime: root.lime
            sy: root.sy
        }

        Item {
            width: parent.width
            height: root.stringH
            z: 2

            Row {
                id: stringRow
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                anchors.verticalCenterOffset: Math.round(-6 * root.sy)
                spacing: Math.round(24 * root.sx)
                height: Math.round(160 * root.sy)
                Repeater {
                    model: backend.stringModel
                    delegate: Item {
                        required property int number
                        required property string letter
                        required property string accidental
                        required property string label
                        required property bool active
                        width: Math.round(118 * root.sx)
                        height: stringRow.height

                        readonly property int ringD: Math.round(101 * root.sx)

                        Repeater {
                            model: active ? 3 : 0
                            Rectangle {
                                required property int index
                                anchors.horizontalCenter: parent.horizontalCenter
                                y: ring.y + ring.height / 2 - height / 2
                                width: ringD + 6 + index * 6
                                height: width
                                radius: width / 2
                                color: "transparent"
                                border.width: 3
                                border.color: root.lime
                                opacity: 0.22 - index * 0.06
                                enabled: false
                            }
                        }

                        Rectangle {
                            id: ring
                            width: ringD
                            height: ringD
                            radius: ringD / 2
                            color: "#0d0d0d"
                            border.width: active ? 1.4 : 1.2
                            border.color: active ? root.lime : "#50504e"
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: Math.round(8 * root.sy)
                        }

                        Rectangle {
                            visible: active
                            anchors.centerIn: ring
                            width: ring.width - 5
                            height: width
                            radius: width / 2
                            color: "transparent"
                            border.width: 1
                            border.color: "#ffffff"
                            opacity: 0.28
                        }

                        Row {
                            anchors.centerIn: ring
                            spacing: accidental === "" ? 0 : Math.round(2 * root.sx)

                            Text {
                                text: letter
                                color: "#ffffff"
                                font.family: root.fontBold
                                font.pixelSize: Math.round(40 * root.sx)
                                font.weight: Font.Bold
                            }

                            Accidental {
                                kind: accidental
                                ink: "#ffffff"
                                fontFamily: root.fontMusic
                                width: Math.round(22 * root.sx)
                                height: Math.round(40 * root.sy)
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }

                        Text {
                            text: label
                            color: "#8e8e8c"
                            font.family: root.fontMedium
                            font.pixelSize: Math.round(24 * root.sy)
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.top: ring.bottom
                            anchors.topMargin: Math.round(6 * root.sy)
                        }

                        MouseArea {
                            anchors.fill: parent
                            z: 3
                            onClicked: backend.selectString(number)
                        }
                    }
                }
            }
        }

        Item {
            id: presetStrip
            width: parent.width
            height: root.chipH
            z: 2

            readonly property int arrowW: Math.round(32 * root.sx)
            readonly property int gap: Math.round(12 * root.sx)
            readonly property int chipCount: Math.max(1, backend.presetModel.count)
            readonly property int chipW: Math.round(252 * root.sx)
            readonly property int chipHgt: Math.round(50 * root.sy)

            Canvas {
                id: chevLeft
                width: presetStrip.arrowW
                height: Math.round(presetStrip.chipHgt * 0.92)
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: chipRow.left
                anchors.rightMargin: presetStrip.gap
                antialiasing: true
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.strokeStyle = "#c8c8c4"
                    ctx.lineWidth = 2
                    ctx.lineCap = "round"
                    ctx.lineJoin = "round"
                    ctx.beginPath()
                    ctx.moveTo(width * 0.64, height * 0.22)
                    ctx.lineTo(width * 0.32, height * 0.50)
                    ctx.lineTo(width * 0.64, height * 0.78)
                    ctx.stroke()
                }
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -8
                    onClicked: backend.cyclePreset(-1)
                }
            }

            Row {
                id: chipRow
                anchors.centerIn: parent
                spacing: presetStrip.gap
                Repeater {
                    model: backend.presetModel
                    Chip {
                        required property string key
                        required property string name
                        required property bool active
                        width: presetStrip.chipW
                        height: presetStrip.chipHgt
                        label: name
                        selected: active
                        fontFamily: root.fontChip
                        lime: root.lime
                        onTapped: backend.selectPreset(key)
                    }
                }
            }

            Canvas {
                id: chevRight
                width: presetStrip.arrowW
                height: Math.round(presetStrip.chipHgt * 0.92)
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: chipRow.right
                anchors.leftMargin: presetStrip.gap
                antialiasing: true
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                onPaint: {
                    const ctx = getContext("2d")
                    ctx.clearRect(0, 0, width, height)
                    ctx.strokeStyle = "#c8c8c4"
                    ctx.lineWidth = 2
                    ctx.lineCap = "round"
                    ctx.lineJoin = "round"
                    ctx.beginPath()
                    ctx.moveTo(width * 0.36, height * 0.22)
                    ctx.lineTo(width * 0.68, height * 0.50)
                    ctx.lineTo(width * 0.36, height * 0.78)
                    ctx.stroke()
                }
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -8
                    onClicked: backend.cyclePreset(1)
                }
            }
        }

        Item {
            width: parent.width
            height: root.statusH

            Row {
                id: statusRow
                anchors.right: parent.right
                anchors.rightMargin: Math.round(88 * root.sx)
                anchors.bottom: parent.bottom
                anchors.bottomMargin: Math.round(28 * root.sy)
                spacing: Math.round(8 * root.sx)
                height: Math.max(20, Math.round(24 * root.sy))

                Canvas {
                    id: lockMark
                    objectName: "lockMark"
                    width: statusRow.height
                    height: statusRow.height
                    antialiasing: true
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Connections {
                        target: backend
                        function onFrameChanged() { lockMark.requestPaint() }
                    }
                    onPaint: {
                        const ctx = getContext("2d")
                        ctx.clearRect(0, 0, width, height)
                        const locked = backend.locked
                        const scale = width / 24
                        ctx.save()
                        ctx.scale(scale, scale)
                        ctx.strokeStyle = locked ? "#3be85c" : "#f0880e"
                        ctx.lineWidth = 2.2
                        ctx.lineCap = "round"
                        ctx.lineJoin = "round"

                        // Lucide lock / unlock (24×24) — same shapes as 🔒 / 🔓 emoji.
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
                        if (locked) {
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
                }

                Item {
                    visible: backend.showSignalMeter
                    width: 1
                    height: parent.height

                    Rectangle {
                        width: 1
                        height: Math.round(parent.height * 0.7)
                        color: "#3a3a38"
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                SignalBars {
                    visible: backend.showSignalMeter
                    filled: backend.signalBars
                    lime: root.lime
                    barHeight: statusRow.height
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
