import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Rectangle {
    id: root
    height: 220
    color: "white"
    border.color: Material.color(Material.Grey, Material.Shade200)
    border.width: 1
    radius: 12
    
    // Drop shadow effect
    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 2
        anchors.leftMargin: 2
        color: "#10000000"
        radius: parent.radius
        z: -1
    }
    
    property var blogItem
    property int itemIndex
    
    signal tagsChanged(string tags)
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20
        
        // Image preview area
        Rectangle {
            Layout.preferredWidth: 140
            Layout.preferredHeight: 180
            color: Material.color(Material.Grey, Material.Shade100)
            border.color: Material.color(Material.Grey, Material.Shade300)
            border.width: 1
            radius: 8
            
            Image {
                id: blogImage
                anchors.fill: parent
                anchors.margins: 2
                fillMode: Image.PreserveAspectFit
                source: {
                    if (!blogItem || !blogItem.imagePath) return ""
                    
                    // Build absolute path to image
                    var imageName = blogItem.imagePath
                    if (imageName.includes("/")) {
                        imageName = imageName.split("/").pop()
                    }
                    return "file://" + blogBackend.getProjectRoot() + "/blog-processor/images/" + imageName
                }
                
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    visible: blogImage.status === Image.Error || !blogItem.imagePath
                    
                    Text {
                        anchors.centerIn: parent
                        text: "📷\nNo Image"
                        horizontalAlignment: Text.AlignHCenter
                        color: Material.color(Material.Grey, Material.Shade600)
                        font.pixelSize: 12
                    }
                }
            }
        }
        
        // Blog content area
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12
            
            // Title editing area
            RowLayout {
                Layout.fillWidth: true
                
                TextField {
                    id: titleField
                    text: blogItem ? blogItem.title : ""
                    font.pixelSize: 17
                    font.bold: true
                    font.family: "Arial"
                    Layout.fillWidth: true
                    placeholderText: "Blog title..."
                    selectByMouse: true
                    
                    background: Rectangle {
                        color: "transparent"
                        border.color: titleField.activeFocus ? Material.color(Material.Blue) : "transparent"
                        border.width: titleField.activeFocus ? 2 : 0
                        radius: 4
                    }
                    
                    onTextChanged: {
                        if (blogItem && text.trim() !== blogItem.title) {
                            blogBackend.updateItemTitle(itemIndex, text)
                        }
                    }
                }
                
                Rectangle {
                    width: 16
                    height: 16
                    radius: 8
                    color: {
                        if (!blogItem) return Material.color(Material.Grey)
                        switch(blogItem.status) {
                            case "pending": return Material.color(Material.Orange)
                            case "processing": return Material.color(Material.Blue)
                            case "completed": return Material.color(Material.Green)
                            case "published": return Material.color(Material.Green)
                            case "error": return Material.color(Material.Red)
                            default: return Material.color(Material.Grey)
                        }
                    }
                    
                    ToolTip {
                        visible: statusMouseArea.containsMouse
                        text: blogItem ? blogItem.status : ""
                    }
                    
                    MouseArea {
                        id: statusMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                }
            }
            
            // PDF path
            Text {
                text: blogItem ? "📄 " + blogItem.pdfPath.split('/').pop() : ""
                font.pixelSize: 12
                font.family: "Arial"
                color: Material.color(Material.Grey, Material.Shade500)
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            
            // Excerpt preview
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                Layout.maximumHeight: 50
                clip: true
                
                Text {
                    text: blogItem && blogItem.excerpt ? blogItem.excerpt : "Preview will appear after processing..."
                    font.pixelSize: 12
                    font.family: "Arial"
                    color: Material.color(Material.Grey, Material.Shade600)
                    width: parent.width
                    wrapMode: Text.WordWrap
                }
            }
            
            // Tags input area
            RowLayout {
                Layout.fillWidth: true
                spacing: 15
                
                Text {
                    text: "Tags:"
                    font.pixelSize: 13
                    font.family: "Arial"
                    font.bold: true
                    color: Material.color(Material.Grey, Material.Shade700)
                    Layout.alignment: Qt.AlignVCenter
                }
                
                TextField {
                    id: tagsField
                    Layout.fillWidth: true
                    placeholderText: "Enter tags separated by commas (e.g., food, phoenix, restaurants)"
                    text: blogItem && blogItem.tags ? blogItem.tags.join(", ") : ""
                    font.pixelSize: 12
                    font.family: "Arial"
                    selectByMouse: true
                    
                    background: Rectangle {
                        color: Material.color(Material.Grey, Material.Shade50)
                        border.color: tagsField.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                        border.width: 1
                        radius: 6
                    }
                    
                    onTextChanged: {
                        if (text.trim() !== "") {
                            root.tagsChanged(text)
                        }
                    }
                }
                
                Button {
                    text: {
                        if (!blogItem) return "Process"
                        switch(blogItem.status) {
                            case "published": return "Update"
                            case "processing": return "Processing..."
                            case "completed": return "Update"
                            case "error": return "Retry"
                            default: return "Process"
                        }
                    }
                    enabled: blogItem && blogItem.status !== "processing" && tagsField.text.trim() !== ""
                    
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "Arial"
                    
                    implicitWidth: 90
                    implicitHeight: 35
                    
                    Material.background: {
                        if (!enabled) return Material.Grey
                        if (!blogItem) return Material.Grey
                        switch(blogItem.status) {
                            case "published": return Material.Blue
                            case "processing": return Material.Blue
                            case "completed": return Material.Blue
                            case "error": return Material.Red
                            default: return Material.Orange
                        }
                    }
                    
                    Material.foreground: "white"
                    
                    onClicked: {
                        if (blogItem && tagsField.text.trim() !== "") {
                            if (blogItem.status === "published" || blogItem.status === "completed") {
                                blogBackend.updatePublishedBlog(itemIndex)
                            } else {
                                blogBackend.processSingleItem(itemIndex)
                            }
                        }
                    }
                }
            }
            
            // Status indicator  
            Rectangle {
                Layout.fillWidth: true
                height: 28
                color: {
                    if (!blogItem) return "transparent"
                    switch(blogItem.status) {
                        case "published": return Material.color(Material.Green, Material.Shade100)
                        case "pending": return Material.color(Material.Orange, Material.Shade100) 
                        case "processing": return Material.color(Material.Blue, Material.Shade100)
                        case "completed": return Material.color(Material.Green, Material.Shade100)
                        case "error": return Material.color(Material.Red, Material.Shade100)
                        default: return "transparent"
                    }
                }
                radius: 6
                border.color: {
                    if (!blogItem) return "transparent"
                    switch(blogItem.status) {
                        case "published": return Material.color(Material.Green, Material.Shade300)
                        case "pending": return Material.color(Material.Orange, Material.Shade300) 
                        case "processing": return Material.color(Material.Blue, Material.Shade300)
                        case "completed": return Material.color(Material.Green, Material.Shade300)
                        case "error": return Material.color(Material.Red, Material.Shade300)
                        default: return "transparent"
                    }
                }
                border.width: 1
                
                Text {
                    anchors.centerIn: parent
                    text: {
                        if (!blogItem) return ""
                        switch(blogItem.status) {
                            case "published": return "✅ Already Published"
                            case "pending": return "⏳ Ready to Process"
                            case "processing": return "🔄 Processing..."
                            case "completed": return "✅ Completed"
                            case "error": return "❌ Error"
                            default: return ""
                        }
                    }
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "Arial"
                    color: Material.color(Material.Grey, Material.Shade700)
                }
            }
        }
    }
}