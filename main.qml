import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

ApplicationWindow {
    id: root
    visible: true
    width: 1200
    height: 800
    title: "Agent Skills MVP - Workflow Automation"
    
    color: "#f5f5f5"
    
    // Python backend connection
    Connections {
        target: backend
        
        function onScanCompleted(result) {
            statusText.text = "✓ Scan completed: " + result.issues_found + " issues found"
            scanResults.text = JSON.stringify(result, null, 2)
            currentStep.text = "Step 1: Scan ✓"
            progressBar.value = 25
        }
        
        function onPlanCreated(plan) {
            statusText.text = "✓ Plan created with " + plan.steps.length + " steps"
            planResults.text = JSON.stringify(plan, null, 2)
            currentStep.text = "Step 2: Plan ✓"
            progressBar.value = 50
        }
        
        function onValidationCompleted(result) {
            statusText.text = result.is_valid ? "✓ Plan validated" : "✗ Validation failed"
            validationResults.text = JSON.stringify(result, null, 2)
            currentStep.text = "Step 3: Validate " + (result.is_valid ? "✓" : "✗")
            progressBar.value = 75
        }
        
        function onSimulationCompleted(result) {
            statusText.text = result.success ? "✓ Simulation successful" : "✗ Simulation failed"
            simulationResults.text = result.output
            currentStep.text = "Step 4: Simulate " + (result.success ? "✓" : "✗")
            progressBar.value = 100
        }
    }
    
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15
        
        // Header
        Rectangle {
            Layout.fillWidth: true
            height: 60
            color: "#2c3e50"
            radius: 5
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 20
                
                Text {
                    text: "Agent Skills MVP"
                    font.pixelSize: 24
                    font.bold: true
                    color: "white"
                }
                
                Text {
                    text: currentStep.text
                    font.pixelSize: 14
                    color: "#ecf0f1"
                    Layout.fillWidth: true
                }
            }
        }
        
        Text {
            id: currentStep
            text: "Ready to start"
            visible: false
        }
        
        // Input Section
        Rectangle {
            Layout.fillWidth: true
            height: 80
            color: "white"
            border.color: "#bdc3c7"
            border.width: 1
            radius: 5
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 15
                spacing: 10
                
                Text {
                    text: "Folder Path:"
                    font.pixelSize: 12
                    font.bold: true
                }
                
                TextField {
                    id: folderInput
                    Layout.fillWidth: true
                    placeholderText: "Enter folder path (e.g., /home/user/project)"
                    text: "/home/ubuntu/agent-skills"
                }
                
                Button {
                    text: "Browse"
                    onClicked: folderDialog.open()
                }
                
                Button {
                    text: "Start Workflow"
                    background: Rectangle {
                        color: "#27ae60"
                        radius: 3
                    }
                    contentItem: Text {
                        text: parent.text
                        color: "white"
                        font.bold: true
                    }
                    onClicked: {
                        statusText.text = "Starting workflow..."
                        progressBar.value = 0
                        backend.startWorkflow(folderInput.text)
                    }
                }
            }
        }
        
        // Progress Bar
        ProgressBar {
            id: progressBar
            Layout.fillWidth: true
            from: 0
            to: 100
            value: 0
            height: 8
        }
        
        // Status
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "#ecf0f1"
            radius: 3
            
            Text {
                id: statusText
                anchors.fill: parent
                anchors.margins: 10
                text: "Ready to scan folder"
                font.pixelSize: 12
                verticalAlignment: Text.AlignVCenter
            }
        }
        
        // Results Tabs
        TabBar {
            id: tabBar
            Layout.fillWidth: true
            
            TabButton {
                text: "Scan Results"
            }
            TabButton {
                text: "Plan"
            }
            TabButton {
                text: "Validation"
            }
            TabButton {
                text: "Simulation"
            }
            TabButton {
                text: "Report"
            }
        }
        
        // Tab Content
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex
            
            // Scan Results Tab
            Rectangle {
                color: "white"
                border.color: "#bdc3c7"
                border.width: 1
                radius: 3
                
                ScrollView {
                    anchors.fill: parent
                    
                    TextEdit {
                        id: scanResults
                        text: "Scan results will appear here..."
                        readOnly: true
                        font.family: "Courier"
                        font.pixelSize: 10
                        padding: 10
                        selectByMouse: true
                    }
                }
            }
            
            // Plan Tab
            Rectangle {
                color: "white"
                border.color: "#bdc3c7"
                border.width: 1
                radius: 3
                
                ScrollView {
                    anchors.fill: parent
                    
                    TextEdit {
                        id: planResults
                        text: "Plan will appear here..."
                        readOnly: true
                        font.family: "Courier"
                        font.pixelSize: 10
                        padding: 10
                        selectByMouse: true
                    }
                }
            }
            
            // Validation Tab
            Rectangle {
                color: "white"
                border.color: "#bdc3c7"
                border.width: 1
                radius: 3
                
                ScrollView {
                    anchors.fill: parent
                    
                    TextEdit {
                        id: validationResults
                        text: "Validation results will appear here..."
                        readOnly: true
                        font.family: "Courier"
                        font.pixelSize: 10
                        padding: 10
                        selectByMouse: true
                    }
                }
            }
            
            // Simulation Tab
            Rectangle {
                color: "white"
                border.color: "#bdc3c7"
                border.width: 1
                radius: 3
                
                ScrollView {
                    anchors.fill: parent
                    
                    TextEdit {
                        id: simulationResults
                        text: "Simulation output will appear here..."
                        readOnly: true
                        font.family: "Courier"
                        font.pixelSize: 10
                        padding: 10
                        selectByMouse: true
                    }
                }
            }
            
            // Report Tab
            Rectangle {
                color: "white"
                border.color: "#bdc3c7"
                border.width: 1
                radius: 3
                
                ScrollView {
                    anchors.fill: parent
                    
                    TextEdit {
                        id: reportResults
                        text: "Final report will appear here..."
                        readOnly: true
                        font.family: "Courier"
                        font.pixelSize: 10
                        padding: 10
                        selectByMouse: true
                    }
                }
            }
        }
        
        // Footer
        Rectangle {
            Layout.fillWidth: true
            height: 40
            color: "#34495e"
            radius: 3
            
            RowLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 20
                
                Text {
                    text: "Agent Skills MVP v1.0"
                    color: "#ecf0f1"
                    font.pixelSize: 10
                }
                
                Item {
                    Layout.fillWidth: true
                }
                
                Button {
                    text: "Export Report"
                    onClicked: {
                        reportDialog.open()
                    }
                }
            }
        }
    }
    
    // File dialogs
    FolderDialog {
        id: folderDialog
        onAccepted: {
            folderInput.text = selectedFolder.toString().replace("file://", "")
        }
    }
    
    FileDialog {
        id: reportDialog
        fileMode: FileDialog.SaveFile
        nameFilters: ["JSON files (*.json)"]
        onAccepted: {
            // Export report
            statusText.text = "Report exported to: " + selectedFile
        }
    }
}
