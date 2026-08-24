import QtQuick

Item {
    id: root
    property string fontMedium: "Inter"
    property string fontSemi: "Inter"
    property string fontChip: "Inter"

    function back() {
        if (backend.pickingDevice)
            backend.closeDevicePicker()
        else
            backend.closeSettings()
    }

    Column {
        anchors.fill: parent

        Item {
            width: parent.width
            height: 52

            Text {
                text: "‹  " + (backend.pickingDevice ? "Settings" : "Tuner")
                color: "#2ee164"
                font.family: root.fontChip
                font.pixelSize: 16
                anchors.left: parent.left
                anchors.leftMargin: 28
                anchors.verticalCenter: parent.verticalCenter
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -8
                    onClicked: root.back()
                }
            }

            Text {
                text: backend.pickingDevice ? "Input Device" : "Settings"
                color: "#ffffff"
                font.family: root.fontSemi
                font.pixelSize: 22
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
            }

            Text {
                text: "BASS TUNER"
                color: "#a8a8a8"
                font.family: root.fontMedium
                font.pixelSize: 15
                anchors.right: parent.right
                anchors.rightMargin: 28
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Flickable {
            id: flick
            width: parent.width
            height: parent.height - 52 - 78
            clip: true
            contentWidth: width
            contentHeight: inner.height
            boundsBehavior: Flickable.StopAtBounds

            Item {
                id: inner
                width: flick.width
                height: pageLoader.height + 26

                Loader {
                    id: pageLoader
                    x: 40
                    y: 10
                    width: inner.width - 80
                    sourceComponent: backend.pickingDevice ? devicePage : mainPage
                }
            }
        }

        Item {
            width: parent.width
            height: 78

            Text {
                text: backend.appVersion + " · Apache-2.0"
                color: "#b0b0b0"
                font.family: root.fontMedium
                font.pixelSize: 13
                anchors.horizontalCenter: parent.horizontalCenter
                y: 4
            }

            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                y: 22
                spacing: 14
                visible: !backend.pickingDevice

                Chip {
                    label: "Reset Defaults"
                    fontFamily: root.fontChip
                    height: 40
                    implicitWidth: 180
                    onTapped: backend.resetDefaults()
                }
                Chip {
                    label: "Done"
                    selected: true
                    fontFamily: root.fontChip
                    height: 40
                    implicitWidth: 180
                    onTapped: backend.closeSettings()
                }
            }

            Chip {
                visible: backend.pickingDevice
                label: "Back"
                selected: true
                fontFamily: root.fontChip
                height: 40
                implicitWidth: 180
                anchors.horizontalCenter: parent.horizontalCenter
                y: 22
                onTapped: backend.closeDevicePicker()
            }
        }
    }

    component SettingsRow: Item {
        property string label: ""
        default property alias content: slot.data
        width: parent.width
        height: 36
        Text {
            text: label
            color: "#b0b0b0"
            font.family: root.fontMedium
            font.pixelSize: 13
            anchors.verticalCenter: parent.verticalCenter
        }
        Item {
            id: slot
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            height: parent.height
            width: 300
        }
    }

    component SectionLabel: Text {
        width: parent.width
        color: "#a8a8a8"
        font.family: root.fontMedium
        font.pixelSize: 15
        topPadding: 4
        bottomPadding: 8
    }

    component Divider: Rectangle {
        width: parent.width
        height: 1
        color: "#383838"
        opacity: 1
    }

    Component {
        id: devicePage
        Column {
            width: pageLoader.width
            spacing: 8

            Text {
                text: "Tap a device to select"
                color: "#b0b0b0"
                font.family: root.fontMedium
                font.pixelSize: 13
            }

            Repeater {
                model: backend.deviceModel
                Chip {
                    required property int devIndex
                    required property string name
                    required property bool active
                    width: pageLoader.width
                    height: 36
                    label: name
                    selected: active
                    fontFamily: root.fontChip
                    onTapped: backend.selectDevice(devIndex)
                }
            }

            Text {
                visible: backend.deviceModel.count <= 1
                text: "No extra inputs found — System Default still works"
                color: "#b0b0b0"
                font.family: root.fontMedium
                font.pixelSize: 13
            }
        }
    }

    Component {
        id: mainPage
        Column {
            width: pageLoader.width
            spacing: 0

            SectionLabel { text: "AUDIO" }

            SettingsRow {
                label: "Input Device"
                Chip {
                    anchors.right: parent.right
                    width: 300
                    height: 32
                    label: backend.deviceLabel
                    chevron: true
                    fontFamily: root.fontChip
                    onTapped: backend.openDevicePicker()
                }
            }

            SettingsRow {
                label: "Input Level"
                Row {
                    anchors.right: parent.right
                    spacing: 12
                    height: parent.height
                    SignalBars {
                        filled: backend.energyBars
                        barHeight: 16
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Chip {
                        label: "Calibrate"
                        selected: backend.notice.indexOf("Calibrated") === 0
                        fontFamily: root.fontChip
                        height: 32
                        implicitWidth: 108
                        anchors.verticalCenter: parent.verticalCenter
                        onTapped: backend.calibrate()
                    }
                }
            }

            Text {
                visible: backend.notice.length > 0
                width: parent.width
                text: backend.notice
                color: backend.notice.indexOf("Calibrated") === 0 ? "#2ee164" : "#b0b0b0"
                font.family: root.fontMedium
                font.pixelSize: 13
                bottomPadding: 8
            }

            Divider { }

            SectionLabel { text: "TUNING"; topPadding: 10 }

            SettingsRow {
                label: "Reference Pitch"
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Chip {
                        label: "−"
                        implicitWidth: 48
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.nudgeA4(-1)
                    }
                    Chip {
                        label: backend.a4Hz + " Hz"
                        selected: true
                        implicitWidth: 108
                        height: 32
                        fontFamily: root.fontChip
                    }
                    Chip {
                        label: "+"
                        implicitWidth: 48
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.nudgeA4(1)
                    }
                }
            }

            SettingsRow {
                label: "In-Tune Threshold"
                SettingSlider {
                    anchors.fill: parent
                    fontFamily: root.fontChip
                    from: 1
                    to: 10
                    value: backend.inTuneCents
                    valueText: "±" + Math.round(backend.inTuneCents) + "¢"
                    loLabel: "±1¢"
                    hiLabel: "±10¢"
                    onMoved: (v) => backend.setInTune(Math.round(v))
                }
            }

            SettingsRow {
                label: "String Detection"
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Chip {
                        label: "Auto"
                        selected: backend.stringAuto
                        implicitWidth: 88
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setStringAuto(true)
                    }
                    Chip {
                        label: "Manual"
                        selected: !backend.stringAuto
                        implicitWidth: 88
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setStringAuto(false)
                    }
                }
            }

            SettingsRow {
                label: "Response Speed"
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Chip {
                        label: "Slow"
                        selected: backend.response === "slow"
                        implicitWidth: 76
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setResponse("slow")
                    }
                    Chip {
                        label: "Normal"
                        selected: backend.response === "normal"
                        implicitWidth: 76
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setResponse("normal")
                    }
                    Chip {
                        label: "Fast"
                        selected: backend.response === "fast"
                        implicitWidth: 76
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setResponse("fast")
                    }
                }
            }

            Divider { }

            SectionLabel { text: "DETECTION"; topPadding: 10 }

            SettingsRow {
                label: "Min Confidence"
                SettingSlider {
                    anchors.fill: parent
                    fontFamily: root.fontChip
                    from: 0.10
                    to: 0.50
                    value: backend.minConfidence
                    valueText: backend.minConfidence.toFixed(2)
                    loLabel: "0.10"
                    hiLabel: "0.50"
                    onMoved: (v) => backend.setMinConfidence(v)
                }
            }
            SettingsRow {
                label: "Signal Gate"
                SettingSlider {
                    anchors.fill: parent
                    fontFamily: root.fontChip
                    from: 0.002
                    to: 0.020
                    value: backend.signalGate
                    valueText: backend.signalGate.toFixed(3)
                    loLabel: "Low"
                    hiLabel: "High"
                    onMoved: (v) => backend.setSignalGate(v)
                }
            }
            SettingsRow {
                label: "Ringing Hold"
                SettingSlider {
                    anchors.fill: parent
                    fontFamily: root.fontChip
                    from: 0.006
                    to: 0.030
                    value: backend.ringingHold
                    valueText: backend.ringingHold.toFixed(3)
                    loLabel: "Low"
                    hiLabel: "High"
                    onMoved: (v) => backend.setRingingHold(v)
                }
            }

            Divider { }

            SectionLabel { text: "DISPLAY"; topPadding: 10 }

            SettingsRow {
                label: "Needle Smoothing"
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Chip {
                        label: "On"
                        selected: backend.needleSmoothing
                        implicitWidth: 64
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setNeedleSmoothing(true)
                    }
                    Chip {
                        label: "Off"
                        selected: !backend.needleSmoothing
                        implicitWidth: 64
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setNeedleSmoothing(false)
                    }
                }
            }

            SettingsRow {
                label: "Show Signal Meter"
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Chip {
                        label: "On"
                        selected: backend.showSignalMeter
                        implicitWidth: 64
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setShowSignal(true)
                    }
                    Chip {
                        label: "Off"
                        selected: !backend.showSignalMeter
                        implicitWidth: 64
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setShowSignal(false)
                    }
                }
            }

            SettingsRow {
                label: "Cents Bar Range"
                Row {
                    anchors.right: parent.right
                    spacing: 8
                    Chip {
                        label: "±50"
                        selected: backend.centsRange === 50
                        implicitWidth: 64
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setCentsRange(50)
                    }
                    Chip {
                        label: "±25"
                        selected: backend.centsRange === 25
                        implicitWidth: 64
                        height: 32
                        fontFamily: root.fontChip
                        onTapped: backend.setCentsRange(25)
                    }
                }
            }
        }
    }
}
