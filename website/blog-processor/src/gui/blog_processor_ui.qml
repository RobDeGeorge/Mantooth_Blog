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
        
        property int savedCurrentPage: 0
        
        onStatusChanged: {
            statusLabel.text = status
        }
        
        onProcessingFinished: {
            // Processing finished - could add status update here if needed
        }
        
        onPreserveCurrentPage: {
            // Save current page before refresh
            savedCurrentPage = mainContentArea.currentPage
        }
        
        onItemsChanged: {
            // Restore current page after refresh
            mainContentArea.currentPage = savedCurrentPage
        }
        
        Component.onCompleted: {
            // Auto-scan for PDFs when the app starts
            scanForPdfs()
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
            
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                
                Text {
                    text: "🦷 Mantooth Blog Processor"
                    font.pixelSize: 22
                    font.bold: true
                    font.family: "Arial"
                    color: "white"
                }
                
                Text {
                    text: "Transform PDFs into beautiful blog posts"
                    font.pixelSize: 11
                    font.family: "Arial"
                    color: "white"
                    opacity: 0.8
                }
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
    
    // Status and help bar
    Rectangle {
        id: statusBar
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 70
        color: Material.color(Material.Grey, Material.Shade50)
        border.color: Material.color(Material.Grey, Material.Shade200)
        border.width: 1
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 10
            spacing: 5
            
            Text {
                id: statusLabel
                text: "Loading PDFs..."
                font.pixelSize: 14
                font.bold: true
                font.family: "Arial"
                color: Material.color(Material.Grey, Material.Shade700)
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
            
            Text {
                text: "💡 Quick start: 1) Content is auto-loaded from PDFs 2) Add tags to each blog 3) Edit content directly in the text boxes 4) Click 'Process' to publish"
                font.pixelSize: 11
                font.family: "Arial"
                color: Material.color(Material.Grey, Material.Shade600)
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }
    
    // Main content area with pagination
    Rectangle {
        id: mainContentArea
        anchors.top: statusBar.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        anchors.topMargin: 20
        anchors.bottomMargin: 20
        
        color: "transparent"
        
        property int currentPage: 0
        property int totalPages: 0
        
        Component.onCompleted: {
            totalPages = blogBackend.blogModel.rowCount()
        }
        
        // Navigation bar
        Rectangle {
            id: navigationBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: 60
            color: Material.color(Material.Grey, Material.Shade50)
            border.color: Material.color(Material.Grey, Material.Shade200)
            border.width: 1
            radius: 8
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 20
                
                Button {
                    id: prevButton
                    text: "⬅️ Previous"
                    enabled: mainContentArea.currentPage > 0
                    font.pixelSize: 14
                    font.bold: true
                    implicitWidth: 120
                    implicitHeight: 35
                    Material.background: enabled ? Material.Blue : Material.Grey
                    Material.foreground: "white"
                    
                    onClicked: {
                        if (mainContentArea.currentPage > 0) {
                            mainContentArea.currentPage--
                        }
                    }
                }
                
                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "transparent"
                    
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 2
                        
                        Text {
                            text: mainContentArea.totalPages === 0 ? "No blogs found" : 
                                  "Blog " + (mainContentArea.currentPage + 1) + " of " + mainContentArea.totalPages
                            font.pixelSize: 16
                            font.bold: true
                            font.family: "Arial"
                            color: Material.color(Material.Grey, Material.Shade700)
                            Layout.alignment: Qt.AlignHCenter
                        }
                        
                        Text {
                            text: "📄 Navigate through your blog posts"
                            font.pixelSize: 11
                            font.family: "Arial"
                            color: Material.color(Material.Grey, Material.Shade500)
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
                
                Button {
                    id: nextButton
                    text: "Next ➡️"
                    enabled: mainContentArea.currentPage < mainContentArea.totalPages - 1
                    font.pixelSize: 14
                    font.bold: true
                    implicitWidth: 120
                    implicitHeight: 35
                    Material.background: enabled ? Material.Blue : Material.Grey
                    Material.foreground: "white"
                    
                    onClicked: {
                        if (mainContentArea.currentPage < mainContentArea.totalPages - 1) {
                            mainContentArea.currentPage++
                        }
                    }
                }
            }
        }
        
        // Single blog card container
        Rectangle {
            anchors.top: navigationBar.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: 20
            
            color: "transparent"
            
            // Use Repeater instead of Loader to preserve component state
            Repeater {
                id: blogCardRepeater
                model: blogBackend.blogModel
                
                delegate: BlogItemCard {
                    anchors.fill: parent
                    visible: index === mainContentArea.currentPage
                    blogItem: model
                    itemIndex: index
                    
                    onTagsChanged: function(tags) {
                        blogBackend.updateItemTags(index, tags)
                    }
                }
            }
            
            // Show empty state if no items
            Rectangle {
                anchors.fill: parent
                visible: mainContentArea.totalPages === 0
                color: Material.color(Material.Grey, Material.Shade50)
                border.color: Material.color(Material.Grey, Material.Shade200)
                border.width: 1
                radius: 12
                
                ColumnLayout {
                    anchors.centerIn: parent
                    spacing: 20
                    
                    Text {
                        text: "📝"
                        font.pixelSize: 48
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: "No Blog Posts Found"
                        font.pixelSize: 24
                        font.bold: true
                        font.family: "Arial"
                        color: Material.color(Material.Grey, Material.Shade700)
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: "Add PDF files to the input folder to get started"
                        font.pixelSize: 14
                        font.family: "Arial"
                        color: Material.color(Material.Grey, Material.Shade500)
                        Layout.alignment: Qt.AlignHCenter
                    }
                }
            }
        }
        
        // Update total pages when model changes
        Connections {
            target: blogBackend.blogModel
            function onRowsInserted() {
                mainContentArea.totalPages = blogBackend.blogModel.rowCount()
            }
            function onRowsRemoved() {
                mainContentArea.totalPages = blogBackend.blogModel.rowCount()
                // Adjust current page if needed
                if (mainContentArea.currentPage >= mainContentArea.totalPages && mainContentArea.totalPages > 0) {
                    mainContentArea.currentPage = mainContentArea.totalPages - 1
                }
            }
            function onModelReset() {
                mainContentArea.totalPages = blogBackend.blogModel.rowCount()
                mainContentArea.currentPage = 0
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