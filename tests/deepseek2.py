from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QTreeWidget, QTreeWidgetItem, QTextEdit, QPushButton, 
                               QLabel, QScrollArea, QFrame, QSplitter)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SQL Server Compare")
        self.resize(1040, 585)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Create and add the top frame
        self._create_top_frame(main_layout)
        
        # Create a splitter for the middle section
        middle_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(middle_splitter)
        
        # Add treeview and comparison area to the splitter
        self._create_treeview(middle_splitter)
        self._create_comparison_area(middle_splitter)
        
        # Create and add the bottom info bar
        self._create_bottom_info_bar(main_layout)
        
        # Set initial state
        self.source_connection = None
        self.target_connection = None
        self.diff_procedures = []
        self.to_create_procedures = []
        
    def _create_top_frame(self, parent_layout):
        # Top frame with buttons
        top_frame = QFrame()
        top_frame.setFixedHeight(60)
        top_frame.setStyleSheet("background-color: white;")
        top_layout = QHBoxLayout(top_frame)
        top_layout.setContentsMargins(5, 5, 5, 5)
        
        # Compare button
        btn_compare = QPushButton("Compare")
        btn_compare.setFixedSize(80, 25)
        btn_compare.setStyleSheet("background-color: #F0F0F0;")
        btn_compare.clicked.connect(self._on_compare_click)
        top_layout.addWidget(btn_compare)
        
        # Filter button
        btn_filter = QPushButton("Filter")
        btn_filter.setFixedSize(50, 25)
        btn_filter.setStyleSheet("background-color: #F0F0F0;")
        # btn_filter.clicked.connect(self._on_filter_click)
        top_layout.addWidget(btn_filter)
        
        # Spacer
        top_layout.addStretch()
        
        # Source and target buttons in a horizontal layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Select Source button
        self.btn_select_source = QPushButton("Select source")
        self.btn_select_source.setStyleSheet("background-color: #F0F0F0;")
        # self.btn_select_source.clicked.connect(self._on_select_source_click)
        buttons_layout.addWidget(self.btn_select_source, 1)
        
        # Select Target button
        self.btn_select_target = QPushButton("Select target")
        self.btn_select_target.setStyleSheet("background-color: #F0F0F0;")
        # self.btn_select_target.clicked.connect(self._on_select_target_click)
        buttons_layout.addWidget(self.btn_select_target, 1)
        
        top_layout.addLayout(buttons_layout, 2)
        
        parent_layout.addWidget(top_frame)
    
    def _create_treeview(self, parent):
        # Treeview for objects
        self.treeview = QTreeWidget()
        self.treeview.setHeaderLabels(["Object Name", "Object Type", "Action"])
        self.treeview.setColumnCount(3)
        self.treeview.setStyleSheet("background-color: white;")
        self.treeview.itemClicked.connect(self._on_treeview_click)
        
        # Configure column widths
        self.treeview.setColumnWidth(0, 300)
        self.treeview.setColumnWidth(1, 150)
        self.treeview.setColumnWidth(2, 100)
        
        parent.addWidget(self.treeview)
    
    def _create_comparison_area(self, parent):
        # Comparison area with source and target text
        comparison_widget = QWidget()
        comparison_layout = QHBoxLayout(comparison_widget)
        comparison_layout.setContentsMargins(0, 0, 0, 0)
        comparison_layout.setSpacing(5)
        
        # Line numbers widget
        self.line_numbers = QTextEdit()
        self.line_numbers.setReadOnly(True)
        self.line_numbers.setFixedWidth(40)
        self.line_numbers.setStyleSheet("background-color: #F0F0F0;")
        comparison_layout.addWidget(self.line_numbers)
        
        # Splitter for source and target
        text_splitter = QSplitter(Qt.Horizontal)
        
        # Source text
        self.text_source_body = QTextEdit()
        self.text_source_body.setReadOnly(True)
        self.text_source_body.setStyleSheet("background-color: white;")
        text_splitter.addWidget(self.text_source_body)
        
        # Target text
        self.text_target_body = QTextEdit()
        self.text_target_body.setReadOnly(True)
        self.text_target_body.setStyleSheet("background-color: white;")
        text_splitter.addWidget(self.text_target_body)
        
        text_splitter.setSizes([500, 500])
        comparison_layout.addWidget(text_splitter, 1)
        
        parent.addWidget(comparison_widget)
        
        # Configure scroll synchronization
        self.text_source_body.verticalScrollBar().valueChanged.connect(
            lambda: self._sync_scroll(self.text_source_body, self.text_target_body)
        )
        self.text_target_body.verticalScrollBar().valueChanged.connect(
            lambda: self._sync_scroll(self.text_target_body, self.text_source_body)
        )
    
    def _sync_scroll(self, source, target):
        # Synchronize scrolling between two QTextEdit widgets
        source_bar = source.verticalScrollBar()
        target_bar = target.verticalScrollBar()
        
        # Disconnect signals temporarily to prevent infinite recursion
        target_bar.valueChanged.disconnect()
        target_bar.setValue(source_bar.value())
        target_bar.valueChanged.connect(
            lambda: self._sync_scroll(target, source)
        )
        
        # Update line numbers
        self._update_line_numbers()
    
    def _update_line_numbers(self):
        # Update the line numbers widget
        source_lines = self.text_source_body.document().blockCount()
        target_lines = self.text_target_body.document().blockCount()
        max_lines = max(source_lines, target_lines)
        
        self.line_numbers.clear()
        for i in range(1, max_lines + 1):
            self.line_numbers.append(str(i))
    
    def _create_bottom_info_bar(self, parent_layout):
        # Bottom info bar with modification dates
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(20)
        bottom_frame.setStyleSheet("background-color: #F0F0F0; border: 1px solid #C0C0C0;")
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(10, 0, 10, 0)
        
        # Source date label
        self.lbl_source_date = QLabel("Última modificação: -")
        self.lbl_source_date.setStyleSheet("background-color: #F0F0F0;")
        bottom_layout.addWidget(self.lbl_source_date, 1, Qt.AlignLeft)
        
        # Target date label
        self.lbl_target_date = QLabel("Última modificação: -")
        self.lbl_target_date.setStyleSheet("background-color: #F0F0F0;")
        bottom_layout.addWidget(self.lbl_target_date, 1, Qt.AlignRight)
        
        parent_layout.addWidget(bottom_frame)
    
    def _on_compare_click(self):
        # Placeholder for compare functionality
        print("Compare clicked")
        
        # For demonstration, populate with sample data
        self._populate_sample_data()
    
    def _populate_sample_data(self):
        # Clear existing items
        self.treeview.clear()
        
        # Add sample items
        item1 = QTreeWidgetItem(["SampleProcedure1", "Procedure", "Alter"])
        item2 = QTreeWidgetItem(["SampleProcedure2", "Procedure", "Create"])
        
        self.treeview.addTopLevelItem(item1)
        self.treeview.addTopLevelItem(item2)
        
        # Store sample diff data
        self.diff_procedures = [{
            'id': 1,
            'procedure_name': "SampleProcedure1",
            'source_body': [
                "++Line 1 added in source",
                "  Line 2 same",
                "--Line 3 removed from source",
                "~~Line 4 modified in source",
                "  Line 5 same"
            ],
            'target_body': [
                "  Line 2 same",
                "++Line 3 added in target",
                "~~Line 4 modified in target",
                "  Line 5 same",
                "--Line 6 removed from target"
            ],
            'source_modified': "2023-11-15 14:30",
            'target_modified': "2023-11-14 09:45"
        }]
        
        self.to_create_procedures = [{
            'id': 2,
            'procedure_name': "SampleProcedure2",
            'procedure_body': "CREATE PROCEDURE SampleProcedure2 AS\nBEGIN\n    SELECT * FROM Table1\nEND",
            'last_modified_date': "2023-11-16 10:20"
        }]
    
    def _on_treeview_click(self, item, column):
        # Handle treeview item click
        iid = self.treeview.indexOfTopLevelItem(item)
        action = item.text(2)
        
        # Clear text areas
        self.text_source_body.clear()
        self.text_target_body.clear()
        
        # Configure text formats for highlighting
        added_format = QTextCharFormat()
        added_format.setBackground(QColor("pale green"))
        
        removed_format = QTextCharFormat()
        removed_format.setBackground(QColor("misty rose"))
        
        modified_format = QTextCharFormat()
        modified_format.setBackground(QColor("light goldenrod"))
        
        if action == "Alter" and iid < len(self.diff_procedures):
            # Show diff for altered procedure
            diff = self.diff_procedures[iid]
            
            # Insert source text with highlighting
            cursor = self.text_source_body.textCursor()
            for line in diff['source_body']:
                if line.startswith("++"):
                    cursor.insertText(line[2:] + "\n", added_format)
                elif line.startswith("--"):
                    cursor.insertText(line[2:] + "\n", removed_format)
                elif line.startswith("~~"):
                    cursor.insertText(line[2:] + "\n", modified_format)
                else:
                    cursor.insertText(line + "\n")
            
            # Insert target text with highlighting
            cursor = self.text_target_body.textCursor()
            for line in diff['target_body']:
                if line.startswith("++"):
                    cursor.insertText(line[2:] + "\n", added_format)
                elif line.startswith("--"):
                    cursor.insertText(line[2:] + "\n", removed_format)
                elif line.startswith("~~"):
                    cursor.insertText(line[2:] + "\n", modified_format)
                else:
                    cursor.insertText(line + "\n")
            
            # Update modification dates
            self.lbl_source_date.setText(f"Última modificação: {diff['source_modified']}")
            self.lbl_target_date.setText(f"Última modificação: {diff['target_modified']}")
        
        elif action == "Create" and (iid - len(self.diff_procedures)) < len(self.to_create_procedures):
            # Show create procedure
            proc = self.to_create_procedures[iid - len(self.diff_procedures)]
            
            # Insert source text
            self.text_source_body.setPlainText(proc['procedure_body'])
            
            # Clear target text
            self.text_target_body.clear()
            
            # Update modification date
            self.lbl_source_date.setText(f"Última modificação: {proc['last_modified_date']}")
            self.lbl_target_date.setText("Última modificação: -")
        
        # Update line numbers
        self._update_line_numbers()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())