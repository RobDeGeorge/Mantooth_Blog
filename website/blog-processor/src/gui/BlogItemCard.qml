import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Rectangle {
    id: root
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
    
    property var blogItem: null
    property int itemIndex: -1
    
    signal tagsChanged(string tags)
    
    // Hide the entire card if no blog item
    visible: blogItem !== null
    
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24
        
        // Image preview area
        Rectangle {
            Layout.preferredWidth: 160
            Layout.preferredHeight: 220
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
                    return blogBackend.getImagePath(blogItem.imagePath)
                }
                
                onStatusChanged: {
                    if (status === Image.Error) {
                        console.log("Image load error for:", blogItem ? blogItem.title : "unknown", "path:", source)
                    } else if (status === Image.Ready) {
                        console.log("Image loaded successfully for:", blogItem ? blogItem.title : "unknown")
                    }
                }
                
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    visible: blogImage.status === Image.Error || !blogItem || !blogItem.imagePath
                    
                    Text {
                        anchors.centerIn: parent
                        text: "📷\nClick to\nSelect Image"
                        horizontalAlignment: Text.AlignHCenter
                        color: Material.color(Material.Grey, Material.Shade600)
                        font.pixelSize: 11
                        lineHeight: 0.9
                    }
                }
                
                MouseArea {
                    anchors.fill: parent
                    onClicked: imageSelectionPopup.open()
                }
            }
            
            // Image selection popup
            Popup {
                id: imageSelectionPopup
                width: 400
                height: 500
                x: (parent.width - width) / 2
                y: (parent.height - height) / 2
                modal: true
                focus: true
                
                Rectangle {
                    anchors.fill: parent
                    color: "white"
                    border.color: Material.color(Material.Grey, Material.Shade300)
                    border.width: 1
                    radius: 8
                    
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 15
                        
                        Text {
                            text: "Select Image for: " + (blogItem ? blogItem.title : "")
                            font.pixelSize: 16
                            font.bold: true
                            Layout.fillWidth: true
                        }
                        
                        ScrollView {
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            clip: true
                            
                            ListView {
                                id: imageListView
                                model: blogBackend.getAvailableImages()
                                spacing: 8
                                
                                delegate: Rectangle {
                                    width: imageListView.width
                                    height: 80
                                    color: imageMouseArea.containsMouse ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                                    border.color: Material.color(Material.Grey, Material.Shade200)
                                    border.width: 1
                                    radius: 4
                                    
                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.margins: 10
                                        spacing: 15
                                        
                                        Image {
                                            Layout.preferredWidth: 60
                                            Layout.preferredHeight: 60
                                            fillMode: Image.PreserveAspectFit
                                            source: "file://" + blogBackend.getProjectRoot() + "/website/blog-processor/images/" + modelData
                                            
                                            Rectangle {
                                                anchors.fill: parent
                                                color: Material.color(Material.Grey, Material.Shade100)
                                                visible: parent.status === Image.Error
                                                
                                                Text {
                                                    anchors.centerIn: parent
                                                    text: "?"
                                                    font.pixelSize: 20
                                                    color: Material.color(Material.Grey, Material.Shade500)
                                                }
                                            }
                                        }
                                        
                                        Text {
                                            text: modelData
                                            font.pixelSize: 14
                                            Layout.fillWidth: true
                                            wrapMode: Text.WordWrap
                                        }
                                    }
                                    
                                    MouseArea {
                                        id: imageMouseArea
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        onClicked: {
                                            blogBackend.updateItemImage(itemIndex, modelData)
                                            imageSelectionPopup.close()
                                        }
                                    }
                                }
                            }
                        }
                        
                        Button {
                            text: "Cancel"
                            Layout.alignment: Qt.AlignHCenter
                            onClicked: imageSelectionPopup.close()
                        }
                    }
                }
            }
        }
        
        // Blog content area
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16
            
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
                property string pdfFileName: {
                    if (!blogItem || !blogItem.pdfPath) return ""
                    var path = blogItem.pdfPath.toString()
                    return path.substring(path.lastIndexOf('/') + 1)
                }
                text: pdfFileName ? "📄 " + pdfFileName : ""
                font.pixelSize: 12
                font.family: "Arial"
                color: Material.color(Material.Grey, Material.Shade500)
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            
            // Separator
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Material.color(Material.Grey, Material.Shade200)
                Layout.topMargin: 8
                Layout.bottomMargin: 8
            }
            
            // Content editing section
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10
                
                Text {
                    text: "📝 Blog Content:"
                    font.pixelSize: 12
                    font.family: "Arial"
                    font.bold: true
                    color: Material.color(Material.Grey, Material.Shade700)
                }
                
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: 450
                    Layout.preferredHeight: 600
                    clip: true
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    ScrollBar.vertical.policy: ScrollBar.AsNeeded
                    
                    TextArea {
                        id: contentTextArea
                        placeholderText: ""
                        font.pixelSize: 14
                        font.family: "Arial"
                        selectByMouse: true
                        wrapMode: TextArea.Wrap
                        width: parent.width
                        
                        // Add padding to prevent text from touching edges
                        topPadding: 12
                        leftPadding: 12
                        rightPadding: 12
                        bottomPadding: 12
                        
                        // Prevent horizontal scrolling
                        horizontalAlignment: TextArea.AlignLeft
                        verticalAlignment: TextArea.AlignTop
                        
                        property bool isUserEditing: false
                        property string initialContent: (blogItem && blogItem.previewContent) ? blogItem.previewContent : ""
                        
                        // Initialize text but allow editing
                        text: initialContent
                        
                        // Update text when blogItem changes
                        onInitialContentChanged: {
                            if (!isUserEditing) {
                                text = initialContent
                            }
                        }
                        
                        
                        
                        background: Rectangle {
                            color: Material.color(Material.Grey, Material.Shade50)
                            border.color: contentTextArea.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                            border.width: 1
                            radius: 6
                        }
                        
                        onActiveFocusChanged: {
                            if (activeFocus) {
                                isUserEditing = true
                            } else {
                                isUserEditing = false
                                if (text.trim() !== "") {
                                    blogBackend.updatePreviewContent(itemIndex, text)
                                }
                            }
                        }
                        
                        Keys.onPressed: {
                            isUserEditing = true
                        }
                    }
                }
                
            }
            
            // Separator
            Rectangle {
                Layout.fillWidth: true
                height: 1
                color: Material.color(Material.Grey, Material.Shade200)
                Layout.topMargin: 8
                Layout.bottomMargin: 8
            }
            
            // Tags input area
            RowLayout {
                Layout.fillWidth: true
                spacing: 18
                
                Text {
                    text: "🏷️ Tags:"
                    font.pixelSize: 13
                    font.family: "Arial"
                    font.bold: true
                    color: Material.color(Material.Grey, Material.Shade700)
                    Layout.alignment: Qt.AlignVCenter
                }
                
                TextField {
                    id: tagsField
                    Layout.fillWidth: true
                    placeholderText: ""
                    font.pixelSize: 12
                    font.family: "Arial"
                    selectByMouse: true
                    
                    property bool isUserEditing: false
                    property string savedTags: ""
                    
                    Component.onCompleted: {
                        if (blogItem && blogItem.tags) {
                            savedTags = blogItem.tags.join(", ")
                            text = savedTags
                        }
                    }
                    
                    // Watch for blogItem property changes
                    Connections {
                        target: root
                        function onBlogItemChanged() {
                            if (blogItem && blogItem.tags && !tagsField.isUserEditing && tagsField.savedTags === "") {
                                // Only update if we don't have saved tags yet
                                tagsField.savedTags = blogItem.tags.join(", ")
                                tagsField.text = tagsField.savedTags
                            } else if (tagsField.savedTags !== "" && !tagsField.isUserEditing) {
                                // Keep showing saved tags
                                tagsField.text = tagsField.savedTags
                            }
                        }
                    }
                    
                    background: Rectangle {
                        color: Material.color(Material.Grey, Material.Shade50)
                        border.color: tagsField.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                        border.width: 1
                        radius: 6
                    }
                    
                    onActiveFocusChanged: {
                        if (activeFocus) {
                            isUserEditing = true
                        } else {
                            isUserEditing = false
                            if (text.trim() !== "") {
                                savedTags = text.trim()  // Save tags locally
                                root.tagsChanged(text)
                            }
                        }
                    }
                    
                    onTextChanged: {
                        if (isUserEditing && text.trim() !== "") {
                            savedTags = text.trim()  // Save as user types
                        }
                    }
                    
                    Keys.onReturnPressed: {
                        focus = false
                    }
                    
                    Keys.onEnterPressed: {
                        focus = false
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
                    enabled: blogItem && blogItem.status !== "processing" && (tagsField.text.trim() !== "" || (blogItem && blogItem.tags && blogItem.tags.length > 0))
                    
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
                        // First ensure tags are saved
                        if (tagsField.text.trim() !== "") {
                            root.tagsChanged(tagsField.text)
                        }
                        
                        // Then process or update
                        if (blogItem && (tagsField.text.trim() !== "" || (blogItem && blogItem.tags && blogItem.tags.length > 0))) {
                            if (blogItem && (blogItem.status === "published" || blogItem.status === "completed")) {
                                blogBackend.updatePublishedBlog(itemIndex)
                            } else {
                                blogBackend.processSingleItem(itemIndex)
                            }
                        }
                    }
                }
                
                Button {
                    text: "🗑️ Unpublish"
                    enabled: blogItem && blogItem.status === "published"
                    visible: blogItem && blogItem.status === "published"
                    
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "Arial"
                    
                    implicitWidth: 80
                    implicitHeight: 35
                    
                    Material.background: Material.Red
                    Material.foreground: "white"
                    
                    onClicked: {
                        if (blogItem && blogItem.status === "published") {
                            blogBackend.deletePublishedBlog(itemIndex)
                        }
                    }
                }
            }
            
            // Status indicator  
            Rectangle {
                Layout.fillWidth: true
                height: 32
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