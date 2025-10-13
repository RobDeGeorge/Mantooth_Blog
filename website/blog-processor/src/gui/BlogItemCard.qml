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
    
    // Status message component
    Rectangle {
        id: statusMessage
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: 10
        width: statusText.width + 20
        height: statusText.height + 12
        color: isError ? Material.color(Material.Red, Material.Shade100) : Material.color(Material.Green, Material.Shade100)
        border.color: isError ? Material.color(Material.Red, Material.Shade400) : Material.color(Material.Green, Material.Shade400)
        border.width: 1
        radius: 6
        visible: false
        z: 1000
        
        property bool isError: false
        property alias text: statusText.text
        
        Text {
            id: statusText
            anchors.centerIn: parent
            font.pixelSize: 10
            font.bold: true
            color: statusMessage.isError ? Material.color(Material.Red, Material.Shade800) : Material.color(Material.Green, Material.Shade800)
        }
        
        Timer {
            id: statusTimer
            interval: 3000
            onTriggered: statusMessage.visible = false
        }
        
        function showMessage(message, error) {
            statusMessage.text = message
            statusMessage.isError = error || false
            statusMessage.visible = true
            statusTimer.restart()
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: statusMessage.visible = false
        }
    }
    
    
    RowLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 24
        
        // Enhanced image preview area with drag-drop
        Rectangle {
            Layout.preferredWidth: 180
            Layout.preferredHeight: 240
            color: Material.color(Material.Grey, Material.Shade100)
            border.color: {
                if (imageDropArea.containsDrag) return Material.color(Material.Blue, Material.Shade400)
                if (imageMouseArea.containsMouse) return Material.color(Material.Blue, Material.Shade300)
                return Material.color(Material.Grey, Material.Shade300)
            }
            border.width: imageDropArea.containsDrag ? 3 : 1
            radius: 12
            
            // Drag and drop area
            DropArea {
                id: imageDropArea
                anchors.fill: parent
                
                keys: ["text/uri-list"]
                
                onEntered: function(drag) {
                    if (drag.hasUrls) {
                        drag.accepted = true
                    }
                }
                
                onDropped: function(drop) {
                    if (drop.hasUrls) {
                        for (var i = 0; i < drop.urls.length; i++) {
                            var url = drop.urls[i].toString()
                            if (url.startsWith("file://")) {
                                var filePath = url.substring(7) // Remove "file://"
                                handleImageDrop(filePath)
                                break
                            }
                        }
                    }
                }
                
                function handleImageDrop(filePath) {
                    // Extract filename
                    var fileName = filePath.split('/').pop()
                    
                    // Check if it's an image file
                    var imageExtensions = [".png", ".jpg", ".jpeg", ".gif", ".webp"]
                    var isImage = false
                    for (var ext of imageExtensions) {
                        if (fileName.toLowerCase().endsWith(ext)) {
                            isImage = true
                            break
                        }
                    }
                    
                    if (isImage) {
                        // Copy file to images directory and update
                        blogBackend.copyImageToProject(filePath, fileName, itemIndex)
                    } else {
                        // Show error for non-image files
                        statusMessage.showMessage("Please drop an image file (PNG, JPG, GIF, WebP)", true)
                    }
                }
            }
            
            Image {
                id: blogImage
                anchors.fill: parent
                anchors.margins: 4
                fillMode: Image.PreserveAspectFit
                cache: false // Disable cache for live updates
                
                source: {
                    if (!blogItem || !blogItem.imagePath) return ""
                    return blogBackend.getImagePath(blogItem.imagePath) + "?t=" + Date.now()
                }
                
                // Loading indicator
                BusyIndicator {
                    anchors.centerIn: parent
                    visible: blogImage.status === Image.Loading
                    running: visible
                    Material.accent: Material.Blue
                }
                
                onStatusChanged: {
                    if (status === Image.Error) {
                        console.log("Image load error for:", blogItem ? blogItem.title : "unknown", "path:", source)
                    } else if (status === Image.Ready) {
                        console.log("Image loaded successfully for:", blogItem ? blogItem.title : "unknown")
                    }
                }
                
                // Image overlay with info
                Rectangle {
                    anchors.fill: parent
                    color: "transparent"
                    visible: blogImage.status === Image.Error || !blogItem || !blogItem.imagePath
                    
                    Rectangle {
                        anchors.fill: parent
                        color: imageDropArea.containsDrag ? Material.color(Material.Blue, Material.Shade100) : "transparent"
                        opacity: 0.8
                        radius: parent.parent && parent.parent.radius ? parent.parent.radius : 12
                        
                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 8
                            
                            Text {
                                text: imageDropArea.containsDrag ? "📎" : "📷"
                                font.pixelSize: 24
                                Layout.alignment: Qt.AlignHCenter
                                color: imageDropArea.containsDrag ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade600)
                            }
                            
                            Text {
                                text: imageDropArea.containsDrag ? "Drop Image Here" : "Click or Drag\nto Add Image"
                                horizontalAlignment: Text.AlignHCenter
                                color: imageDropArea.containsDrag ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade600)
                                font.pixelSize: 10
                                font.bold: imageDropArea.containsDrag
                                lineHeight: 0.9
                                Layout.alignment: Qt.AlignHCenter
                            }
                        }
                    }
                }
                
                // Image info overlay (shows on hover)
                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 30
                    color: "#80000000"
                    visible: blogImage.status === Image.Ready && imageMouseArea.containsMouse
                    radius: 8
                    
                    Text {
                        anchors.centerIn: parent
                        text: blogItem ? blogItem.imagePath : ""
                        color: "white"
                        font.pixelSize: 9
                        elide: Text.ElideMiddle
                        width: parent.width - 8
                    }
                }
            }
            
            MouseArea {
                id: imageMouseArea
                anchors.fill: parent
                hoverEnabled: true
                onClicked: imageSelectionPopup.open()
                
                cursorShape: Qt.PointingHandCursor
            }
            
            // Enhanced image selection popup with preview
            Popup {
                id: imageSelectionPopup
                width: 600
                height: 500
                x: (parent.parent.width - width) / 2
                y: (parent.parent.height - height) / 2
                modal: true
                focus: true
                
                property string selectedImage: ""
                
                Rectangle {
                    anchors.fill: parent
                    color: "white"
                    border.color: Material.color(Material.Blue, Material.Shade300)
                    border.width: 2
                    radius: 12
                    
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 20
                        spacing: 20
                        
                        // Image list on the left
                        ColumnLayout {
                            Layout.fillHeight: true
                            Layout.preferredWidth: 300
                            spacing: 15
                            
                            Text {
                                text: "🖼️ Select Image for: " + (blogItem ? blogItem.title : "")
                                font.pixelSize: 16
                                font.bold: true
                                Layout.fillWidth: true
                                wrapMode: Text.WordWrap
                            }
                            
                            TextField {
                                id: imageSearchField
                                Layout.fillWidth: true
                                placeholderText: "Search images..."
                                font.pixelSize: 12
                                
                                background: Rectangle {
                                    color: Material.color(Material.Grey, Material.Shade50)
                                    border.color: imageSearchField.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                                    border.width: 1
                                    radius: 6
                                }
                            }
                            
                            ScrollView {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                
                                ListView {
                                    id: imageListView
                                    model: {
                                        var allImages = blogBackend.getAvailableImages()
                                        if (imageSearchField.text.trim() === "") {
                                            return allImages
                                        }
                                        return allImages.filter(function(img) {
                                            return img.toLowerCase().indexOf(imageSearchField.text.toLowerCase()) !== -1
                                        })
                                    }
                                    spacing: 8
                                    
                                    delegate: Rectangle {
                                        width: imageListView.width
                                        height: 80
                                        color: {
                                            if (modelData === imageSelectionPopup.selectedImage) {
                                                return Material.color(Material.Blue, Material.Shade100)
                                            }
                                            return imageItemMouseArea.containsMouse ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                                        }
                                        border.color: {
                                            if (modelData === imageSelectionPopup.selectedImage) {
                                                return Material.color(Material.Blue, Material.Shade400)
                                            }
                                            return Material.color(Material.Grey, Material.Shade200)
                                        }
                                        border.width: modelData === imageSelectionPopup.selectedImage ? 2 : 1
                                        radius: 8
                                        
                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 15
                                            
                                            Image {
                                                Layout.preferredWidth: 60
                                                Layout.preferredHeight: 60
                                                fillMode: Image.PreserveAspectCrop
                                                source: "file://" + blogBackend.getProjectRoot() + "/website/blog-processor/images/" + modelData
                                                
                                                Rectangle {
                                                    anchors.fill: parent
                                                    color: Material.color(Material.Grey, Material.Shade100)
                                                    visible: parent.status === Image.Error
                                                    radius: 4
                                                    
                                                    Text {
                                                        anchors.centerIn: parent
                                                        text: "❌"
                                                        font.pixelSize: 16
                                                    }
                                                }
                                            }
                                            
                                            ColumnLayout {
                                                Layout.fillWidth: true
                                                spacing: 2
                                                
                                                Text {
                                                    text: modelData
                                                    font.pixelSize: 12
                                                    font.bold: true
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                }
                                                
                                                Text {
                                                    text: getImageInfo(modelData)
                                                    font.pixelSize: 10
                                                    color: Material.color(Material.Grey, Material.Shade600)
                                                    Layout.fillWidth: true
                                                    elide: Text.ElideRight
                                                }
                                            }
                                        }
                                        
                                        MouseArea {
                                            id: imageItemMouseArea
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            onClicked: {
                                                imageSelectionPopup.selectedImage = modelData
                                            }
                                            onDoubleClicked: {
                                                blogBackend.updateItemImage(itemIndex, modelData)
                                                imageSelectionPopup.close()
                                            }
                                        }
                                        
                                        function getImageInfo(fileName) {
                                            // Simple file info - could be enhanced with actual file size
                                            return fileName.split('.').pop().toUpperCase() + " image"
                                        }
                                    }
                                }
                            }
                        }
                        
                        // Preview on the right
                        ColumnLayout {
                            Layout.fillHeight: true
                            Layout.fillWidth: true
                            spacing: 15
                            
                            Text {
                                text: "👁️ Preview"
                                font.pixelSize: 16
                                font.bold: true
                            }
                            
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                color: Material.color(Material.Grey, Material.Shade100)
                                border.color: Material.color(Material.Grey, Material.Shade300)
                                border.width: 1
                                radius: 8
                                
                                Image {
                                    id: previewImage
                                    anchors.fill: parent
                                    anchors.margins: 8
                                    fillMode: Image.PreserveAspectFit
                                    source: {
                                        if (imageSelectionPopup.selectedImage) {
                                            return "file://" + blogBackend.getProjectRoot() + "/website/blog-processor/images/" + imageSelectionPopup.selectedImage
                                        }
                                        return ""
                                    }
                                    
                                    Rectangle {
                                        anchors.fill: parent
                                        color: "transparent"
                                        visible: !imageSelectionPopup.selectedImage
                                        
                                        Text {
                                            anchors.centerIn: parent
                                            text: "Select an image\nto preview"
                                            horizontalAlignment: Text.AlignHCenter
                                            color: Material.color(Material.Grey, Material.Shade500)
                                            font.pixelSize: 14
                                        }
                                    }
                                }
                            }
                            
                            RowLayout {
                                Layout.fillWidth: true
                                spacing: 10
                                
                                Button {
                                    text: "Apply"
                                    Layout.fillWidth: true
                                    enabled: imageSelectionPopup.selectedImage !== ""
                                    Material.background: Material.Blue
                                    Material.foreground: "white"
                                    font.bold: true
                                    
                                    onClicked: {
                                        if (imageSelectionPopup.selectedImage) {
                                            blogBackend.updateItemImage(itemIndex, imageSelectionPopup.selectedImage)
                                            imageSelectionPopup.close()
                                        }
                                    }
                                }
                                
                                Button {
                                    text: "Cancel"
                                    Layout.fillWidth: true
                                    onClicked: imageSelectionPopup.close()
                                }
                            }
                        }
                    }
                }
                
                onOpened: {
                    selectedImage = blogItem ? blogItem.imagePath : ""
                    imageSearchField.text = ""
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
                    Layout.minimumHeight: 200
                    Layout.preferredHeight: Math.max(250, Math.min(400, contentTextArea.contentHeight + 50))
                    clip: true
                    
                    // Enhanced scroll bar configuration
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    
                    // Custom scroll bar styling
                    ScrollBar.vertical: ScrollBar {
                        id: verticalScrollBar
                        active: true
                        orientation: Qt.Vertical
                        width: 12
                        
                        background: Rectangle {
                            implicitWidth: 12
                            color: Material.color(Material.Grey, Material.Shade100)
                            opacity: 0.3
                            radius: 6
                        }
                        
                        contentItem: Rectangle {
                            implicitWidth: 8
                            radius: 4
                            color: verticalScrollBar.pressed ? Material.color(Material.Blue, Material.Shade600) : 
                                   verticalScrollBar.hovered ? Material.color(Material.Blue, Material.Shade400) : 
                                   Material.color(Material.Grey, Material.Shade400)
                            opacity: verticalScrollBar.active ? 1.0 : 0.6
                        }
                    }
                    
                    TextArea {
                        id: contentTextArea
                        placeholderText: "Enter your blog content here...\n\nTip: Use double line breaks to separate paragraphs."
                        font.pixelSize: 12
                        font.family: "Arial"
                        selectByMouse: true
                        wrapMode: TextArea.Wrap
                        width: parent.width
                        
                        // Dynamic height based on content
                        height: Math.max(parent.height, contentHeight + topPadding + bottomPadding)
                        
                        // Add padding to prevent text from touching edges
                        topPadding: 16
                        leftPadding: 16
                        rightPadding: 28 // Extra space for scroll bar
                        bottomPadding: 16
                        
                        // Prevent horizontal scrolling
                        horizontalAlignment: TextArea.AlignLeft
                        verticalAlignment: TextArea.AlignTop
                        
                        // Enhanced properties for better UX
                        property bool isUserEditing: false
                        property string initialContent: (blogItem && blogItem.previewContent) ? blogItem.previewContent : ""
                        property bool contentChanged: false
                        property int lastSaveTime: 0
                        
                        // Initialize text but allow editing
                        text: initialContent
                        
                        // Auto-save timer
                        Timer {
                            id: autoSaveTimer
                            interval: 2000 // Auto-save after 2 seconds of inactivity
                            repeat: false
                            onTriggered: {
                                if (contentTextArea.contentChanged && contentTextArea.text.trim() !== "") {
                                    blogBackend.updatePreviewContent(itemIndex, contentTextArea.text)
                                    contentTextArea.contentChanged = false
                                    contentTextArea.lastSaveTime = Date.now()
                                }
                            }
                        }
                        
                        // Update text when blogItem changes
                        onInitialContentChanged: {
                            if (!isUserEditing && !contentChanged) {
                                text = initialContent
                            }
                        }
                        
                        background: Rectangle {
                            color: Material.color(Material.Grey, Material.Shade50)
                            border.color: contentTextArea.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                            border.width: contentTextArea.activeFocus ? 2 : 1
                            radius: 8
                            
                            // Subtle shadow for better visual separation
                            Rectangle {
                                anchors.fill: parent
                                anchors.topMargin: 1
                                anchors.leftMargin: 1
                                color: "#10000000"
                                radius: parent.radius
                                z: -1
                            }
                        }
                        
                        onActiveFocusChanged: {
                            if (activeFocus) {
                                isUserEditing = true
                                autoSaveTimer.stop()
                            } else {
                                isUserEditing = false
                                // Immediate save when losing focus
                                if (contentChanged && text.trim() !== "") {
                                    blogBackend.updatePreviewContent(itemIndex, text)
                                    contentChanged = false
                                    lastSaveTime = Date.now()
                                }
                                autoSaveTimer.stop()
                            }
                        }
                        
                        onTextChanged: {
                            if (isUserEditing) {
                                contentChanged = true
                                autoSaveTimer.restart()
                            }
                        }
                        
                        // Enhanced keyboard handling
                        Keys.onPressed: function(event) {
                            isUserEditing = true
                            
                            // Ctrl+S for manual save
                            if (event.modifiers & Qt.ControlModifier && event.key === Qt.Key_S) {
                                if (contentChanged && text.trim() !== "") {
                                    blogBackend.updatePreviewContent(itemIndex, text)
                                    contentChanged = false
                                    lastSaveTime = Date.now()
                                    autoSaveTimer.stop()
                                }
                                event.accepted = true
                            }
                            // Ctrl+Z for undo
                            else if (event.modifiers & Qt.ControlModifier && event.key === Qt.Key_Z) {
                                undo()
                                event.accepted = true
                            }
                            // Ctrl+Y for redo
                            else if (event.modifiers & Qt.ControlModifier && event.key === Qt.Key_Y) {
                                redo()
                                event.accepted = true
                            }
                        }
                        
                        // Word count indicator
                        property int wordCount: text.trim().split(/\s+/).filter(function(word) { return word.length > 0; }).length
                    }
                    
                    // Word count and save status indicator
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.right: parent.right
                        anchors.margins: 8
                        width: saveStatusText.width + 16
                        height: saveStatusText.height + 8
                        color: Material.color(Material.Grey, Material.Shade100)
                        opacity: 0.9
                        radius: 4
                        visible: contentTextArea.activeFocus || contentTextArea.contentChanged
                        
                        Text {
                            id: saveStatusText
                            anchors.centerIn: parent
                            text: {
                                var status = ""
                                if (contentTextArea.contentChanged) {
                                    status = "●"
                                } else if (contentTextArea.lastSaveTime > 0) {
                                    status = "✓"
                                }
                                return status + " " + contentTextArea.wordCount + " words"
                            }
                            font.pixelSize: 10
                            font.family: "Arial"
                            color: contentTextArea.contentChanged ? Material.color(Material.Orange) : Material.color(Material.Green)
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
                    placeholderText: "Enter tags separated by commas (e.g., travel, food, music)"
                    font.pixelSize: 12
                    font.family: "Arial"
                    selectByMouse: true
                    
                    property bool isUserEditing: false
                    property string savedTags: ""
                    property var suggestedTags: ["travel", "food", "music", "lifestyle", "technology", "art", "photography", "writing"]
                    
                    Component.onCompleted: {
                        if (blogItem && blogItem.tags) {
                            savedTags = blogItem.tags.join(", ")
                            text = savedTags
                        }
                    }
                    
                    // Auto-save timer for tags
                    Timer {
                        id: tagsAutoSaveTimer
                        interval: 1500
                        repeat: false
                        onTriggered: {
                            if (tagsField.text.trim() !== "" && tagsField.text !== tagsField.savedTags) {
                                tagsField.savedTags = tagsField.text.trim()
                                root.tagsChanged(tagsField.text)
                            }
                        }
                    }
                    
                    // Watch for blogItem property changes
                    Connections {
                        target: root
                        function onBlogItemChanged() {
                            if (blogItem && blogItem.tags && !tagsField.isUserEditing && tagsField.savedTags === "") {
                                tagsField.savedTags = blogItem.tags.join(", ")
                                tagsField.text = tagsField.savedTags
                            } else if (tagsField.savedTags !== "" && !tagsField.isUserEditing) {
                                tagsField.text = tagsField.savedTags
                            }
                        }
                    }
                    
                    background: Rectangle {
                        color: Material.color(Material.Grey, Material.Shade50)
                        border.color: tagsField.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                        border.width: tagsField.activeFocus ? 2 : 1
                        radius: 6
                    }
                    
                    onActiveFocusChanged: {
                        if (activeFocus) {
                            isUserEditing = true
                            tagsAutoSaveTimer.stop()
                        } else {
                            isUserEditing = false
                            if (text.trim() !== "" && text !== savedTags) {
                                savedTags = text.trim()
                                root.tagsChanged(text)
                                tagsAutoSaveTimer.stop()
                            }
                        }
                    }
                    
                    onTextChanged: {
                        if (isUserEditing) {
                            tagsAutoSaveTimer.restart()
                        }
                    }
                    
                    Keys.onReturnPressed: {
                        focus = false
                    }
                    
                    Keys.onEnterPressed: {
                        focus = false
                    }
                    
                    // Enhanced validation
                    property bool hasValidTags: {
                        var tags = text.trim().split(",").map(function(tag) { return tag.trim(); }).filter(function(tag) { return tag.length > 0; })
                        return tags.length > 0 && tags.length <= 8 && tags.every(function(tag) { return tag.length <= 20; })
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
                    enabled: blogItem && blogItem.status !== "processing" && (tagsField.hasValidTags)
                    
                    font.pixelSize: 11
                    font.bold: true
                    font.family: "Arial"
                    
                    implicitWidth: 110
                    implicitHeight: 40
                    
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
                    
                    // Enhanced tooltip with error information
                    ToolTip {
                        visible: parent.hovered
                        text: {
                            if (!blogItem) return "No blog item"
                            if (!tagsField.hasValidTags) return "Please add valid tags first"
                            if (blogItem.status === "error") return "Click to retry processing"
                            if (blogItem.status === "processing") return "Processing in progress..."
                            if (blogItem.status === "published") return "Update published blog"
                            return "Process blog for publishing"
                        }
                        delay: 500
                    }
                    
                    onClicked: {
                        try {
                            // Validate tags first
                            if (!tagsField.hasValidTags) {
                                statusMessage.showMessage("❌ Please add valid tags before processing", true)
                                return
                            }
                            
                            // Save tags if changed
                            if (tagsField.text.trim() !== "") {
                                root.tagsChanged(tagsField.text)
                            }
                            
                            // Process or update
                            if (blogItem) {
                                if (blogItem.status === "published" || blogItem.status === "completed") {
                                    blogBackend.updatePublishedBlog(itemIndex)
                                } else {
                                    blogBackend.processSingleItem(itemIndex)
                                }
                            }
                        } catch (error) {
                            statusMessage.showMessage("❌ Failed to process: " + error.toString(), true)
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