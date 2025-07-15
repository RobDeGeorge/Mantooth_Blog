import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import BlogProcessor 1.0

ApplicationWindow {
    id: mainWindow
    width: 1400
    height: 900
    visible: true
    title: "🦷 Mantooth Blog Processor"
    
    Material.theme: Material.Light
    Material.accent: Material.Pink
    Material.primary: Material.DeepOrange
    
    minimumWidth: 1000
    minimumHeight: 600
    
    property alias backend: blogBackend
    
    BlogProcessorBackend {
        id: blogBackend
        
        onStatusChanged: {
            statusLabel.text = status
        }
        
        onProcessingFinished: {
            processAllButton.enabled = true
        }
        
        Component.onCompleted: {
            // Auto-scan for PDFs when the app starts
            blogBackend.scanForPdfs()
        }
    }
    
    // Header
    Rectangle {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: 70
        color: Material.color(Material.DeepOrange)
        
        // Drop shadow effect
        Rectangle {
            anchors.top: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: 3
            gradient: Gradient {
                GradientStop { position: 0; color: "#40000000" }
                GradientStop { position: 1; color: "transparent" }
            }
        }
        
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 30
            anchors.rightMargin: 30
            anchors.topMargin: 15
            anchors.bottomMargin: 15
            spacing: 20
            
            Text {
                text: "🦷 Mantooth Blog Processor"
                font.pixelSize: 22
                font.bold: true
                font.family: "Arial"
                color: "white"
                Layout.fillWidth: true
            }
            
            Button {
                id: nukeButton
                text: "💥 Nuke All"
                font.pixelSize: 12
                font.bold: true
                Material.background: Material.Red
                Material.foreground: "white"
                implicitWidth: 100
                implicitHeight: 35
                onClicked: confirmDialog.open()
            }
        }
    }
    
    // Status bar
    Rectangle {
        id: statusBar
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 45
        color: Material.color(Material.Grey, Material.Shade50)
        border.color: Material.color(Material.Grey, Material.Shade200)
        border.width: 1
        
        Text {
            id: statusLabel
            anchors.centerIn: parent
            text: "Loading PDFs..."
            font.pixelSize: 14
            font.family: "Arial"
            color: Material.color(Material.Grey, Material.Shade700)
        }
    }
    
    // Main content area
    ScrollView {
        anchors.top: statusBar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 20
        anchors.bottomMargin: 20
        
        clip: true
        
        ListView {
            id: blogListView
            model: blogBackend.blogModel
            spacing: 20
            
            delegate: BlogItemCard {
                width: blogListView.width
                blogItem: model
                itemIndex: index
                onTagsChanged: function(tags) {
                    blogBackend.updateItemTags(index, tags)
                }
            }
            
            // Add some padding at the bottom
            footer: Rectangle {
                width: parent.width
                height: 20
                color: "transparent"
            }
        }
    }
    
    // Confirmation Dialog
    Rectangle {
        id: confirmDialog
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 1000
        
        function open() {
            visible = true
        }
        
        function close() {
            visible = false
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: confirmDialog.close()
        }
        
        Rectangle {
            anchors.centerIn: parent
            width: 480
            height: 260
            color: "white"
            radius: 12
            border.color: Material.color(Material.Red, Material.Shade300)
            border.width: 2
            
            // Drop shadow
            Rectangle {
                anchors.fill: parent
                anchors.topMargin: 4
                anchors.leftMargin: 4
                color: "#40000000"
                radius: parent.radius
                z: -1
            }
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 30
                spacing: 25
                
                Text {
                    text: "💥 Nuclear Option"
                    font.pixelSize: 24
                    font.bold: true
                    font.family: "Arial"
                    color: Material.color(Material.Red)
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Text {
                    text: "This will DELETE ALL published blogs and reset everything to blank.\n\nThis action cannot be undone!\n\nAre you absolutely sure?"
                    font.pixelSize: 15
                    font.family: "Arial"
                    color: Material.color(Material.Grey, Material.Shade800)
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    lineHeight: 1.3
                }
                
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    
                    Button {
                        text: "Cancel"
                        Layout.fillWidth: true
                        font.pixelSize: 14
                        font.bold: true
                        font.family: "Arial"
                        implicitHeight: 45
                        Material.background: Material.Grey
                        Material.foreground: "white"
                        onClicked: confirmDialog.close()
                    }
                    
                    Button {
                        text: "💥 YES, NUKE EVERYTHING"
                        Layout.fillWidth: true
                        font.pixelSize: 14
                        font.bold: true
                        font.family: "Arial"
                        implicitHeight: 45
                        Material.background: Material.Red
                        Material.foreground: "white"
                        onClicked: {
                            confirmDialog.close()
                            blogBackend.nukeAllBlogs()
                        }
                    }
                }
            }
        }
    }
}