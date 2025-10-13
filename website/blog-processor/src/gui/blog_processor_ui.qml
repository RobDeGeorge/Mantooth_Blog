import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import QtQuick.Window 2.15
import BlogProcessor 1.0

ApplicationWindow {
    id: mainWindow
    
    // Dynamic sizing based on available screen space
    Component.onCompleted: {
        var screenGeometry = Screen.desktopAvailableGeometry
        if (screenGeometry && screenGeometry.width && screenGeometry.height) {
            var targetWidth = Math.min(1000, screenGeometry.width * 0.75)
            var targetHeight = Math.min(650, screenGeometry.height * 0.75)
            
            width = targetWidth
            height = targetHeight
            
            // Center the window
            x = (screenGeometry.width - width) / 2
            y = (screenGeometry.height - height) / 2
        } else {
            // Fallback if screen info is not available
            width = 900
            height = 600
        }
    }
    
    visible: true
    title: "🦷 Mantooth Blog Processor"
    
    // Remember window geometry
    property alias windowX: mainWindow.x
    property alias windowY: mainWindow.y
    property alias windowWidth: mainWindow.width
    property alias windowHeight: mainWindow.height
    
    Material.theme: Material.Light
    Material.accent: Material.Pink
    Material.primary: Material.DeepOrange
    
    minimumWidth: 600
    minimumHeight: 450
    
    // Enhanced window properties for better responsiveness
    property bool isCompactMode: width < 1000
    property real contentScale: Math.max(0.6, Math.min(1.0, width / 1200))
    
    // Window flags for better Wayland/X11 compatibility
    flags: Qt.Window | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint | Qt.WindowTitleHint
    
    property alias backend: blogBackend
    
    BlogProcessorBackend {
        id: blogBackend
        
        property int savedCurrentPage: 0
        
        onStatusChanged: {
            statusLabel.text = status
            // Log status changes for debugging
            console.log("Status changed:", status)
        }
        
        // Handle real-time updates
        onRealTimeUpdateSignal: function(index, property, value) {
            console.log("Real-time update:", index, property, value)
            // Could add visual feedback here
        }
        
        // Handle validation messages
        onDataValidationSignal: function(message, isError) {
            if (isError) {
                globalStatusMessage.showMessage("❌ " + message, true)
            } else {
                globalStatusMessage.showMessage("✅ " + message, false)
            }
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
        height: 60
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
            anchors.leftMargin: 20
            anchors.rightMargin: 20
            anchors.topMargin: 10
            anchors.bottomMargin: 10
            spacing: 20
            
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                
                Text {
                    text: "🦷 Mantooth Blog Processor"
                    font.pixelSize: 18
                    font.bold: true
                    font.family: "Arial"
                    color: "white"
                }
                
                Text {
                    text: "Transform PDFs into beautiful blog posts"
                    font.pixelSize: 10
                    font.family: "Arial"
                    color: "white"
                    opacity: 0.8
                }
            }
            
            RowLayout {
                spacing: 10
                
                Button {
                    id: refreshButton
                    text: "🔄 Refresh"
                    font.pixelSize: 11
                    font.bold: true
                    Material.background: Material.Green
                    Material.foreground: "white"
                    implicitWidth: 100
                    implicitHeight: 40
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Refresh blog list (Ctrl+R)"
                        delay: 500
                    }
                    
                    onClicked: blogBackend.scanForPdfs()
                }
                
                Button {
                    id: helpButton
                    text: "❓ Help"
                    font.pixelSize: 11
                    font.bold: true
                    Material.background: Material.Blue
                    Material.foreground: "white"
                    implicitWidth: 90
                    implicitHeight: 40
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Show help (F1)"
                        delay: 500
                    }
                    
                    onClicked: helpOverlay.open()
                }
                
                Button {
                    id: backupButton
                    text: "💾 Backup"
                    font.pixelSize: 11
                    font.bold: true
                    Material.background: Material.Teal
                    Material.foreground: "white"
                    implicitWidth: 100
                    implicitHeight: 40
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Create backup of all blog data"
                        delay: 500
                    }
                    
                    onClicked: backupDialog.open()
                }
                
                Button {
                    id: validateButton
                    text: "✓ Validate"
                    font.pixelSize: 11
                    font.bold: true
                    Material.background: Material.Orange
                    Material.foreground: "white"
                    implicitWidth: 100
                    implicitHeight: 40
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Validate all blog data"
                        delay: 500
                    }
                    
                    onClicked: {
                        blogBackend.validateAllData()
                    }
                }
                
                Button {
                    id: nukeButton
                    text: "💥 Nuke All"
                    font.pixelSize: 11
                    font.bold: true
                    Material.background: Material.Red
                    Material.foreground: "white"
                    implicitWidth: 110
                    implicitHeight: 40
                    
                    ToolTip {
                        visible: parent.hovered
                        text: "Delete all published blogs"
                        delay: 500
                    }
                    
                    onClicked: confirmDialog.open()
                }
            }
        }
    }
    
    // Status and help bar
    Rectangle {
        id: statusBar
        anchors.top: header.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: 60
        color: Material.color(Material.Grey, Material.Shade50)
        border.color: Material.color(Material.Grey, Material.Shade200)
        border.width: 1
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 5
            
            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                
                BusyIndicator {
                    id: statusIndicator
                    visible: blogBackend.status.indexOf("processing") !== -1 || blogBackend.status.indexOf("scanning") !== -1
                    running: visible
                    Material.accent: Material.Blue
                    implicitWidth: 20
                    implicitHeight: 20
                }
                
                Text {
                    id: statusLabel
                    text: "Loading PDFs..."
                    font.pixelSize: 12
                    font.bold: true
                    font.family: "Arial"
                    color: {
                        if (text.indexOf("✅") !== -1 || text.indexOf("completed") !== -1) {
                            return Material.color(Material.Green, Material.Shade700)
                        } else if (text.indexOf("❌") !== -1 || text.indexOf("error") !== -1) {
                            return Material.color(Material.Red, Material.Shade700)
                        } else if (text.indexOf("⏳") !== -1 || text.indexOf("processing") !== -1) {
                            return Material.color(Material.Blue, Material.Shade700)
                        }
                        return Material.color(Material.Grey, Material.Shade700)
                    }
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                    
                    // Auto-clear success/error messages after 5 seconds
                    Timer {
                        id: statusClearTimer
                        interval: 5000
                        onTriggered: {
                            if (statusLabel.text.indexOf("✅") !== -1 || statusLabel.text.indexOf("❌") !== -1) {
                                statusLabel.text = "Ready"
                            }
                        }
                    }
                    
                    onTextChanged: function() {
                        if (text.indexOf("✅") !== -1 || text.indexOf("❌") !== -1) {
                            statusClearTimer.restart()
                        } else {
                            statusClearTimer.stop()
                        }
                    }
                }
                
                // Connection status indicator
                Rectangle {
                    width: 12
                    height: 12
                    radius: 6
                    color: {
                        if (blogBackend.status.indexOf("error") !== -1) {
                            return Material.color(Material.Red)
                        } else if (blogBackend.status.indexOf("processing") !== -1) {
                            return Material.color(Material.Orange)
                        } else if (blogBackend.status.indexOf("completed") !== -1 || blogBackend.status.indexOf("✅") !== -1) {
                            return Material.color(Material.Green)
                        }
                        return Material.color(Material.Grey)
                    }
                    
                    ToolTip {
                        visible: connectionMouseArea.containsMouse
                        text: {
                            if (parent.color === Material.color(Material.Red)) {
                                return "Error state - check logs"
                            } else if (parent.color === Material.color(Material.Orange)) {
                                return "Processing in progress"
                            } else if (parent.color === Material.color(Material.Green)) {
                                return "Operation completed successfully"
                            }
                            return "Ready"
                        }
                    }
                    
                    MouseArea {
                        id: connectionMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                }
            }
            
            Text {
                text: "💡 Quick start: 1) Content is auto-loaded from PDFs 2) Add tags to each blog 3) Edit content directly in the text boxes 4) Click 'Process' to publish"
                font.pixelSize: 10
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
        anchors.leftMargin: 20
        anchors.rightMargin: 20
        anchors.topMargin: 15
        anchors.bottomMargin: 15
        
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
                    font.pixelSize: 12
                    font.bold: true
                    implicitWidth: 140
                    implicitHeight: 40
                    Material.background: enabled ? Material.Blue : Material.Grey
                    Material.foreground: "white"
                    
                    // Enhanced tooltip
                    ToolTip {
                        visible: parent.hovered
                        text: "Previous blog (← or Ctrl+P)"
                        delay: 500
                    }
                    
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
                    font.pixelSize: 12
                    font.bold: true
                    implicitWidth: 140
                    implicitHeight: 40
                    Material.background: enabled ? Material.Blue : Material.Grey
                    Material.foreground: "white"
                    
                    // Enhanced tooltip
                    ToolTip {
                        visible: parent.hovered
                        text: "Next blog (→ or Ctrl+N)"
                        delay: 500
                    }
                    
                    onClicked: {
                        if (mainContentArea.currentPage < mainContentArea.totalPages - 1) {
                            mainContentArea.currentPage++
                        }
                    }
                }
            }
        }
        
        // Enhanced scrollable blog card container
        ScrollView {
            id: mainScrollView
            anchors.top: navigationBar.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: 20
            
            clip: true
            
            // Enhanced scroll bar configuration
            ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
            
            // Custom scroll bar styling
            ScrollBar.vertical: ScrollBar {
                id: mainVerticalScrollBar
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
                    color: mainVerticalScrollBar.pressed ? Material.color(Material.Blue, Material.Shade600) : 
                           mainVerticalScrollBar.hovered ? Material.color(Material.Blue, Material.Shade400) : 
                           Material.color(Material.Grey, Material.Shade400)
                    opacity: mainVerticalScrollBar.active ? 1.0 : 0.6
                }
            }
            
            // Responsive container for blog cards
            Rectangle {
                id: cardContainer
                width: mainScrollView.width
                height: Math.min(mainScrollView.height * 0.9, 600)
                color: "transparent"
                
                // Dynamic sizing based on content
                property int cardMinHeight: Math.min(500, mainScrollView.height - 40)
                property int cardMaxHeight: 600
                
                Item {
                    id: blogCardContent
                    anchors.fill: parent
                    anchors.margins: 20
                    
                    // Use Repeater instead of Loader to preserve component state
                    Repeater {
                        id: blogCardRepeater
                        model: blogBackend.blogModel
                        
                        delegate: BlogItemCard {
                            anchors.fill: parent
                            visible: index === mainContentArea.currentPage
                            blogItem: model
                            itemIndex: index
                            
                            // Enhanced responsive sizing
                            property real scaleFactor: Math.min(1.0, parent.width / 1200)
                            
                            onTagsChanged: function(tags) {
                                blogBackend.updateItemTags(index, tags)
                            }
                            
                            // Update parent height when card content changes
                            onHeightChanged: {
                                if (visible) {
                                    blogCardContent.height = Math.max(
                                        cardContainer.cardMinHeight, 
                                        Math.min(cardContainer.cardMaxHeight, height + 40)
                                    )
                                }
                            }
                        }
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
    
    // Search Overlay
    Rectangle {
        id: searchOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 2000
        
        function open() {
            visible = true
            searchField.forceActiveFocus()
            searchField.selectAll()
        }
        
        function close() {
            visible = false
            searchField.text = ""
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: searchOverlay.close()
        }
        
        Rectangle {
            anchors.centerIn: parent
            width: 500
            height: 400
            color: "white"
            radius: 12
            border.color: Material.color(Material.Blue, Material.Shade300)
            border.width: 2
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 20
                spacing: 15
                
                Text {
                    text: "🔍 Search Blogs"
                    font.pixelSize: 20
                    font.bold: true
                    color: Material.color(Material.Blue)
                    Layout.alignment: Qt.AlignHCenter
                }
                
                TextField {
                    id: searchField
                    Layout.fillWidth: true
                    placeholderText: "Search in titles, content, or tags..."
                    font.pixelSize: 14
                    
                    Keys.onEscapePressed: searchOverlay.close()
                    Keys.onReturnPressed: performSearch()
                    
                    background: Rectangle {
                        color: Material.color(Material.Grey, Material.Shade50)
                        border.color: searchField.activeFocus ? Material.color(Material.Blue) : Material.color(Material.Grey, Material.Shade300)
                        border.width: 2
                        radius: 8
                    }
                }
                
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    
                    ListView {
                        id: searchResults
                        model: ListModel { id: searchResultsModel }
                        spacing: 8
                        
                        delegate: Rectangle {
                            width: searchResults.width
                            height: 60
                            color: searchMouseArea.containsMouse ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                            border.color: Material.color(Material.Grey, Material.Shade200)
                            border.width: 1
                            radius: 8
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 10
                                
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    
                                    Text {
                                        text: model.title || ""
                                        font.pixelSize: 14
                                        font.bold: true
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    
                                    Text {
                                        text: (model.tags || []).join(", ")
                                        font.pixelSize: 10
                                        color: Material.color(Material.Grey, Material.Shade600)
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                }
                                
                                Text {
                                    text: "#" + (model.index + 1)
                                    font.pixelSize: 12
                                    color: Material.color(Material.Blue)
                                    font.bold: true
                                }
                            }
                            
                            MouseArea {
                                id: searchMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    mainContentArea.currentPage = model.index
                                    searchOverlay.close()
                                }
                            }
                        }
                    }
                }
                
                RowLayout {
                    Layout.fillWidth: true
                    
                    Button {
                        text: "Search"
                        Layout.fillWidth: true
                        onClicked: performSearch()
                    }
                    
                    Button {
                        text: "Close"
                        Layout.fillWidth: true
                        onClicked: searchOverlay.close()
                    }
                }
            }
        }
        
        function performSearch() {
            searchResultsModel.clear()
            var searchTerm = searchField.text.toLowerCase().trim()
            
            if (searchTerm === "") {
                return
            }
            
            for (var i = 0; i < blogBackend.blogModel.rowCount(); i++) {
                var item = blogBackend.blogModel.getItem(i)
                if (item) {
                    var matches = false
                    
                    // Search in title
                    if (item.title.toLowerCase().indexOf(searchTerm) !== -1) {
                        matches = true
                    }
                    
                    // Search in tags
                    if (item.tags) {
                        for (var j = 0; j < item.tags.length; j++) {
                            if (item.tags[j].toLowerCase().indexOf(searchTerm) !== -1) {
                                matches = true
                                break
                            }
                        }
                    }
                    
                    // Search in preview content
                    if (item.previewContent && item.previewContent.toLowerCase().indexOf(searchTerm) !== -1) {
                        matches = true
                    }
                    
                    if (matches) {
                        searchResultsModel.append({
                            "title": item.title,
                            "tags": item.tags,
                            "index": i
                        })
                    }
                }
            }
        }
    }
    
    // Help Overlay
    Rectangle {
        id: helpOverlay
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 2000
        
        function open() {
            visible = true
        }
        
        function close() {
            visible = false
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: helpOverlay.close()
        }
        
        Rectangle {
            anchors.centerIn: parent
            width: 600
            height: 500
            color: "white"
            radius: 12
            border.color: Material.color(Material.Blue, Material.Shade300)
            border.width: 2
            
            ScrollView {
                anchors.fill: parent
                anchors.margins: 20
                clip: true
                
                ColumnLayout {
                    width: parent.width
                    spacing: 15
                    
                    Text {
                        text: "📚 Blog Processor Help"
                        font.pixelSize: 24
                        font.bold: true
                        color: Material.color(Material.Blue)
                        Layout.alignment: Qt.AlignHCenter
                    }
                    
                    Text {
                        text: "Keyboard Shortcuts:"
                        font.pixelSize: 16
                        font.bold: true
                        color: Material.color(Material.Grey, Material.Shade700)
                    }
                    
                    Grid {
                        columns: 2
                        columnSpacing: 20
                        rowSpacing: 8
                        Layout.fillWidth: true
                        
                        Text { text: "← / →"; font.family: "Courier"; font.bold: true }
                        Text { text: "Navigate between blogs" }
                        Text { text: "Ctrl + P / N"; font.family: "Courier"; font.bold: true }
                        Text { text: "Previous / Next blog" }
                        Text { text: "Ctrl + F"; font.family: "Courier"; font.bold: true }
                        Text { text: "Search blogs" }
                        Text { text: "Ctrl + R"; font.family: "Courier"; font.bold: true }
                        Text { text: "Refresh blog list" }
                        Text { text: "Ctrl + S"; font.family: "Courier"; font.bold: true }
                        Text { text: "Save current content" }
                        Text { text: "Ctrl + Enter"; font.family: "Courier"; font.bold: true }
                        Text { text: "Process current blog" }
                        Text { text: "F1"; font.family: "Courier"; font.bold: true }
                        Text { text: "Show this help" }
                        Text { text: "Esc"; font.family: "Courier"; font.bold: true }
                        Text { text: "Close overlays" }
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    Text {
                        text: "Workflow:"
                        font.pixelSize: 16
                        font.bold: true
                        color: Material.color(Material.Grey, Material.Shade700)
                    }
                    
                    Text {
                        text: "1. PDFs are automatically loaded from the input folder\n" +
                              "2. Content is extracted and displayed for editing\n" +
                              "3. Add tags to categorize your blog\n" +
                              "4. Select an image from the images folder\n" +
                              "5. Edit the content as needed\n" +
                              "6. Click 'Process' to publish the blog\n" +
                              "7. Use 'Update' to modify published blogs"
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        lineHeight: 1.3
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Material.color(Material.Grey, Material.Shade300)
                    }
                    
                    Text {
                        text: "Tips:"
                        font.pixelSize: 16
                        font.bold: true
                        color: Material.color(Material.Grey, Material.Shade700)
                    }
                    
                    Text {
                        text: "• Content auto-saves after 2 seconds of inactivity\n" +
                              "• Tags are validated (max 8 tags, 20 chars each)\n" +
                              "• Use double line breaks to separate paragraphs\n" +
                              "• Scroll bars appear when content overflows\n" +
                              "• Word count is shown when editing content\n" +
                              "• All actions provide immediate visual feedback"
                        font.pixelSize: 12
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        lineHeight: 1.3
                    }
                    
                    Button {
                        text: "Close Help"
                        Layout.alignment: Qt.AlignHCenter
                        Layout.topMargin: 20
                        onClicked: helpOverlay.close()
                    }
                }
            }
        }
        
        Keys.onEscapePressed: close()
    }
    
    // Backup and Restore Dialog
    Rectangle {
        id: backupDialog
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 3000
        
        function open() {
            visible = true
            refreshBackupList()
        }
        
        function close() {
            visible = false
        }
        
        function refreshBackupList() {
            backupListModel.clear()
            var backups = blogBackend.getAvailableBackups()
            for (var i = 0; i < backups.length; i++) {
                backupListModel.append(backups[i])
            }
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: backupDialog.close()
        }
        
        Rectangle {
            anchors.centerIn: parent
            width: 700
            height: 500
            color: "white"
            radius: 12
            border.color: Material.color(Material.Blue, Material.Shade300)
            border.width: 2
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 30
                spacing: 20
                
                Text {
                    text: "💾 Backup & Restore"
                    font.pixelSize: 24
                    font.bold: true
                    color: Material.color(Material.Blue)
                    Layout.alignment: Qt.AlignHCenter
                }
                
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 15
                    
                    Button {
                        text: "💾 Create Backup"
                        font.pixelSize: 14
                        font.bold: true
                        Material.background: Material.Green
                        Material.foreground: "white"
                        implicitHeight: 40
                        
                        onClicked: {
                            blogBackend.createBackup()
                            backupDialog.refreshBackupList()
                        }
                    }
                    
                    Button {
                        text: "🔄 Refresh List"
                        font.pixelSize: 14
                        onClicked: backupDialog.refreshBackupList()
                    }
                    
                    Button {
                        text: "🔧 Repair Data"
                        font.pixelSize: 14
                        Material.background: Material.Orange
                        Material.foreground: "white"
                        
                        onClicked: {
                            blogBackend.repairDataInconsistencies()
                        }
                    }
                    
                    Item { Layout.fillWidth: true }
                    
                    Button {
                        text: "Close"
                        onClicked: backupDialog.close()
                    }
                }
                
                Text {
                    text: "Available Backups:"
                    font.pixelSize: 16
                    font.bold: true
                    color: Material.color(Material.Grey, Material.Shade700)
                }
                
                ScrollView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    
                    ListView {
                        id: backupListView
                        model: ListModel { id: backupListModel }
                        spacing: 8
                        
                        delegate: Rectangle {
                            width: backupListView.width
                            height: 80
                            color: backupMouseArea.containsMouse ? Material.color(Material.Blue, Material.Shade50) : "transparent"
                            border.color: Material.color(Material.Grey, Material.Shade200)
                            border.width: 1
                            radius: 8
                            
                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 15
                                spacing: 15
                                
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 2
                                    
                                    Text {
                                        text: model.name || "Unknown Backup"
                                        font.pixelSize: 14
                                        font.bold: true
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    
                                    Text {
                                        text: {
                                            var date = new Date(model.date || "")
                                            return "Created: " + date.toLocaleString()
                                        }
                                        font.pixelSize: 10
                                        color: Material.color(Material.Grey, Material.Shade600)
                                        Layout.fillWidth: true
                                    }
                                    
                                    Text {
                                        text: `${model.total_blogs || 0} blogs, ${model.size_mb || 0} MB`
                                        font.pixelSize: 10
                                        color: Material.color(Material.Grey, Material.Shade600)
                                        Layout.fillWidth: true
                                    }
                                }
                                
                                Button {
                                    text: "🔄 Restore"
                                    font.pixelSize: 11
                                    Material.background: Material.Blue
                                    Material.foreground: "white"
                                    implicitWidth: 80
                                    implicitHeight: 30
                                    
                                    onClicked: {
                                        restoreConfirmDialog.backupName = model.name || ""
                                        restoreConfirmDialog.open()
                                    }
                                }
                            }
                            
                            MouseArea {
                                id: backupMouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                            }
                        }
                    }
                }
                
                Text {
                    text: "Tip: Backups are created automatically every 30 minutes when there are published blogs."
                    font.pixelSize: 10
                    color: Material.color(Material.Grey, Material.Shade600)
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }
        }
        
        Keys.onEscapePressed: close()
    }
    
    // Restore Confirmation Dialog
    Rectangle {
        id: restoreConfirmDialog
        anchors.fill: parent
        color: "#80000000"
        visible: false
        z: 3100
        
        property string backupName: ""
        
        function open() {
            visible = true
        }
        
        function close() {
            visible = false
            backupName = ""
        }
        
        MouseArea {
            anchors.fill: parent
            onClicked: restoreConfirmDialog.close()
        }
        
        Rectangle {
            anchors.centerIn: parent
            width: 500
            height: 300
            color: "white"
            radius: 12
            border.color: Material.color(Material.Orange, Material.Shade300)
            border.width: 2
            
            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 30
                spacing: 20
                
                Text {
                    text: "⚠️ Confirm Restore"
                    font.pixelSize: 20
                    font.bold: true
                    color: Material.color(Material.Orange)
                    Layout.alignment: Qt.AlignHCenter
                }
                
                Text {
                    text: `Are you sure you want to restore from backup:\n\n${restoreConfirmDialog.backupName}\n\nThis will:\n• Create a backup of current data\n• Replace all blog data with backup data\n• Refresh the blog list\n\nThis action cannot be easily undone.`
                    font.pixelSize: 14
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
                        onClicked: restoreConfirmDialog.close()
                    }
                    
                    Button {
                        text: "🔄 YES, RESTORE"
                        Layout.fillWidth: true
                        font.pixelSize: 14
                        font.bold: true
                        Material.background: Material.Orange
                        Material.foreground: "white"
                        
                        onClicked: {
                            blogBackend.restoreFromBackup(restoreConfirmDialog.backupName)
                            restoreConfirmDialog.close()
                            backupDialog.close()
                        }
                    }
                }
            }
        }
        
        Keys.onEscapePressed: close()
    }
}