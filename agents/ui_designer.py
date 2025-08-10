from typing import Dict, List, Any, Optional
import json
from .base_agent import BaseAgent
from core.model_orchestrator import AgentType

class UIDesignerAgent(BaseAgent):
    """UI Designer Agent - Specialized in frontend development and user experience design"""
    
    def __init__(self):
        super().__init__(
            name="UI Designer",
            role="Frontend Developer",
            specialization="User interface design, user experience, frontend development, and visual design",
            agent_type=AgentType.UI_DESIGNER
        )
        self.ui_frameworks = {
            "react": {
                "components": ["Button", "Input", "Card", "Modal", "Navigation"],
                "styling": ["CSS Modules", "Styled Components", "Tailwind CSS"]
            },
            "vue": {
                "components": ["v-btn", "v-text-field", "v-card", "v-dialog", "v-navigation-drawer"],
                "styling": ["Vuetify", "Vue CSS", "Tailwind CSS"]
            },
            "html_css": {
                "components": ["button", "input", "div", "nav", "form"],
                "styling": ["Bootstrap", "CSS Grid", "Flexbox"]
            }
        }
    
    def process_request(self, request: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process UI/UX design requests"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"UI/UX design request: {request}\n\nProject context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages)
        
        # Generate UI components and styling
        generated_files = self.generate_ui_files(request, context)
        
        # Determine handoffs
        handoff_to = None
        if any(keyword in request.lower() for keyword in ["test", "testing", "validate"]):
            handoff_to = "test_writer"
        elif any(keyword in request.lower() for keyword in ["backend", "api", "data"]):
            handoff_to = "code_generator"
        elif any(keyword in request.lower() for keyword in ["debug", "fix", "error"]):
            handoff_to = "debugger"
        
        self.add_to_history(request, response_content)
        
        return {
            "content": response_content,
            "handoff_to": handoff_to,
            "agent": self.name,
            "files": generated_files
        }
    
    def process_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process handoff from another agent"""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"Handoff from another agent: {handoff_content}\n\nDesign context: {json.dumps(context, indent=2)}"}
        ]
        
        response_content = self.call_llm(messages, temperature=0.5)
        
        # Generate UI components based on handoff
        generated_files = self.generate_ui_from_handoff(handoff_content, context)
        
        self.add_to_history(f"Handoff: {handoff_content}", response_content)
        
        return {
            "content": f"**UI Designer Implementation:**\n\n{response_content}",
            "agent": self.name,
            "files": generated_files
        }
    
    def generate_ui_files(self, request: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate UI files based on request"""
        files = {}
        
        # Detect UI framework preference
        if any(keyword in request.lower() for keyword in ["react", "jsx"]):
            files.update(self.generate_react_components(request))
        elif any(keyword in request.lower() for keyword in ["vue", "vuejs"]):
            files.update(self.generate_vue_components(request))
        else:
            files.update(self.generate_html_css_components(request))
        
        return files
    
    def generate_react_components(self, request: str) -> Dict[str, str]:
        """Generate React components"""
        files = {}
        
        files["src/App.jsx"] = '''import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent';
import Footer from './components/Footer';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Initialize application
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Fetch data from API
      const response = await fetch('/api/data');
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  return (
    <div className="app">
      <Header 
        onMenuClick={toggleSidebar}
        title="Generated Application"
      />
      
      <div className="app-layout">
        <Sidebar 
          isOpen={sidebarOpen}
          currentPage={currentPage}
          onPageChange={handlePageChange}
          onClose={() => setSidebarOpen(false)}
        />
        
        <MainContent 
          currentPage={currentPage}
          data={data}
          loading={loading}
          onDataUpdate={loadInitialData}
        />
      </div>
      
      <Footer />
    </div>
  );
}

export default App;
'''
        
        files["src/components/Header.jsx"] = '''import React from 'react';
import './Header.css';

const Header = ({ onMenuClick, title }) => {
  return (
    <header className="header">
      <div className="header-left">
        <button 
          className="menu-button"
          onClick={onMenuClick}
          aria-label="Toggle menu"
        >
          <span className="hamburger"></span>
          <span className="hamburger"></span>
          <span className="hamburger"></span>
        </button>
        <h1 className="header-title">{title}</h1>
      </div>
      
      <div className="header-right">
        <nav className="header-nav">
          <button className="nav-button">Notifications</button>
          <button className="nav-button">Settings</button>
          <div className="user-menu">
            <button className="user-button">
              <span className="user-avatar">U</span>
              <span className="user-name">User</span>
            </button>
          </div>
        </nav>
      </div>
    </header>
  );
};

export default Header;
'''
        
        files["src/components/Sidebar.jsx"] = '''import React from 'react';
import './Sidebar.css';

const Sidebar = ({ isOpen, currentPage, onPageChange, onClose }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'products', label: 'Products', icon: '📦' },
    { id: 'orders', label: 'Orders', icon: '🛒' },
    { id: 'customers', label: 'Customers', icon: '👥' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
    { id: 'settings', label: 'Settings', icon: '⚙️' }
  ];

  return (
    <>
      {isOpen && <div className="sidebar-overlay" onClick={onClose}></div>}
      
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <h2>Menu</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>
        
        <nav className="sidebar-nav">
          <ul className="nav-list">
            {menuItems.map(item => (
              <li key={item.id} className="nav-item">
                <button
                  className={`nav-link ${currentPage === item.id ? 'active' : ''}`}
                  onClick={() => onPageChange(item.id)}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>
        
        <div className="sidebar-footer">
          <button className="logout-button">
            <span className="nav-icon">🚪</span>
            <span className="nav-label">Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
'''
        
        files["src/components/MainContent.jsx"] = '''import React from 'react';
import './MainContent.css';
import Dashboard from './pages/Dashboard';
import ProductList from './pages/ProductList';
import OrderList from './pages/OrderList';

const MainContent = ({ currentPage, data, loading, onDataUpdate }) => {
  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard data={data} loading={loading} />;
      case 'products':
        return <ProductList data={data} loading={loading} onUpdate={onDataUpdate} />;
      case 'orders':
        return <OrderList data={data} loading={loading} onUpdate={onDataUpdate} />;
      case 'customers':
        return <div className="page">Customers Page</div>;
      case 'analytics':
        return <div className="page">Analytics Page</div>;
      case 'settings':
        return <div className="page">Settings Page</div>;
      default:
        return <Dashboard data={data} loading={loading} />;
    }
  };

  return (
    <main className="main-content">
      <div className="content-container">
        {loading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Loading...</p>
          </div>
        ) : (
          renderPage()
        )}
      </div>
    </main>
  );
};

export default MainContent;
'''
        
        files["src/App.css"] = '''/* Global Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f5f5;
  color: #333;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* Header Styles */
.header {
  background: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.menu-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.menu-button:hover {
  background-color: #f0f0f0;
}

.hamburger {
  width: 20px;
  height: 2px;
  background-color: #333;
  border-radius: 1px;
}

.header-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  color: #666;
  font-size: 14px;
}

.nav-button:hover {
  background-color: #f0f0f0;
  color: #333;
}

.user-menu .user-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 20px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

/* Sidebar Styles */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.sidebar {
  position: fixed;
  top: 0;
  left: -280px;
  width: 280px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e0e0e0;
  transition: left 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.sidebar-open {
  left: 0;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.close-button {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
}

.sidebar-nav {
  flex: 1;
  padding: 20px 0;
}

.nav-list {
  list-style: none;
}

.nav-item {
  margin-bottom: 5px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  transition: background-color 0.2s;
}

.nav-link:hover {
  background-color: #f8f9fa;
}

.nav-link.active {
  background-color: #e3f2fd;
  color: #1976d2;
}

.nav-icon {
  font-size: 18px;
}

/* Main Content Styles */
.main-content {
  flex: 1;
  overflow-y: auto;
  background-color: #f8f9fa;
}

.content-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #007bff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Responsive Design */
@media (min-width: 768px) {
  .sidebar {
    position: static;
    left: 0;
    width: 250px;
  }
  
  .sidebar-overlay {
    display: none;
  }
  
  .close-button {
    display: none;
  }
}

@media (max-width: 767px) {
  .header-title {
    font-size: 18px;
  }
  
  .content-container {
    padding: 15px;
  }
}
'''
        
        return files
    
    def generate_vue_components(self, request: str) -> Dict[str, str]:
        """Generate Vue.js components"""
        files = {}
        
        files["src/App.vue"] = '''<template>
  <div id="app">
    <AppHeader 
      :title="appTitle"
      @toggle-sidebar="toggleSidebar"
    />
    
    <div class="app-layout">
      <AppSidebar 
        :is-open="sidebarOpen"
        :current-page="currentPage"
        @page-change="handlePageChange"
        @close="closeSidebar"
      />
      
      <MainContent 
        :current-page="currentPage"
        :data="data"
        :loading="loading"
        @data-update="loadData"
      />
    </div>
    
    <AppFooter />
  </div>
</template>

<script>
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import MainContent from './components/MainContent.vue'
import AppFooter from './components/AppFooter.vue'

export default {
  name: 'App',
  components: {
    AppHeader,
    AppSidebar,
    MainContent,
    AppFooter
  },
  data() {
    return {
      appTitle: 'Generated Vue Application',
      sidebarOpen: false,
      currentPage: 'dashboard',
      data: [],
      loading: false
    }
  },
  mounted() {
    this.loadData()
  },
  methods: {
    toggleSidebar() {
      this.sidebarOpen = !this.sidebarOpen
    },
    closeSidebar() {
      this.sidebarOpen = false
    },
    handlePageChange(page) {
      this.currentPage = page
      this.closeSidebar()
    },
    async loadData() {
      this.loading = true
      try {
        const response = await fetch('/api/data')
        if (response.ok) {
          this.data = await response.json()
        }
      } catch (error) {
        console.error('Error loading data:', error)
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: #f5f5f5;
  color: #333;
}
</style>
'''
        
        files["src/components/AppHeader.vue"] = '''<template>
  <header class="app-header">
    <div class="header-left">
      <button 
        class="menu-button"
        @click="$emit('toggle-sidebar')"
        aria-label="Toggle menu"
      >
        <span class="hamburger"></span>
        <span class="hamburger"></span>
        <span class="hamburger"></span>
      </button>
      <h1 class="header-title">{{ title }}</h1>
    </div>
    
    <div class="header-right">
      <nav class="header-nav">
        <button class="nav-button">🔔 Notifications</button>
        <button class="nav-button">⚙️ Settings</button>
        <div class="user-menu">
          <button class="user-button">
            <span class="user-avatar">U</span>
            <span class="user-name">User</span>
          </button>
        </div>
      </nav>
    </div>
  </header>
</template>

<script>
export default {
  name: 'AppHeader',
  props: {
    title: {
      type: String,
      default: 'Application'
    }
  },
  emits: ['toggle-sidebar']
}
</script>

<style scoped>
.app-header {
  background: #ffffff;
  border-bottom: 1px solid #e0e0e0;
  padding: 0 20px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.menu-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.menu-button:hover {
  background-color: #f0f0f0;
}

.hamburger {
  width: 20px;
  height: 2px;
  background-color: #333;
  border-radius: 1px;
}

.header-title {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 15px;
}

.nav-button {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  color: #666;
  font-size: 14px;
}

.nav-button:hover {
  background-color: #f0f0f0;
  color: #333;
}

.user-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 20px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #007bff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}
</style>
'''
        
        return files
    
    def generate_html_css_components(self, request: str) -> Dict[str, str]:
        """Generate HTML/CSS components"""
        files = {}
        
        files["index.html"] = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Web Application</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app">
        <!-- Header -->
        <header class="header">
            <div class="header-left">
                <button class="menu-button" id="menuToggle" aria-label="Toggle menu">
                    <i class="fas fa-bars"></i>
                </button>
                <h1 class="header-title">Generated Application</h1>
            </div>
            
            <div class="header-right">
                <nav class="header-nav">
                    <button class="nav-button">
                        <i class="fas fa-bell"></i>
                        <span>Notifications</span>
                    </button>
                    <button class="nav-button">
                        <i class="fas fa-cog"></i>
                        <span>Settings</span>
                    </button>
                    <div class="user-menu">
                        <button class="user-button">
                            <span class="user-avatar">U</span>
                            <span class="user-name">User</span>
                        </button>
                    </div>
                </nav>
            </div>
        </header>

        <!-- App Layout -->
        <div class="app-layout">
            <!-- Sidebar -->
            <aside class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <h2>Menu</h2>
                    <button class="close-button" id="sidebarClose">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <nav class="sidebar-nav">
                    <ul class="nav-list">
                        <li class="nav-item">
                            <a href="#dashboard" class="nav-link active" data-page="dashboard">
                                <i class="fas fa-chart-bar nav-icon"></i>
                                <span class="nav-label">Dashboard</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="#products" class="nav-link" data-page="products">
                                <i class="fas fa-box nav-icon"></i>
                                <span class="nav-label">Products</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="#orders" class="nav-link" data-page="orders">
                                <i class="fas fa-shopping-cart nav-icon"></i>
                                <span class="nav-label">Orders</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="#customers" class="nav-link" data-page="customers">
                                <i class="fas fa-users nav-icon"></i>
                                <span class="nav-label">Customers</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="#analytics" class="nav-link" data-page="analytics">
                                <i class="fas fa-chart-line nav-icon"></i>
                                <span class="nav-label">Analytics</span>
                            </a>
                        </li>
                        <li class="nav-item">
                            <a href="#settings" class="nav-link" data-page="settings">
                                <i class="fas fa-cog nav-icon"></i>
                                <span class="nav-label">Settings</span>
                            </a>
                        </li>
                    </ul>
                </nav>
                
                <div class="sidebar-footer">
                    <button class="logout-button">
                        <i class="fas fa-sign-out-alt nav-icon"></i>
                        <span class="nav-label">Logout</span>
                    </button>
                </div>
            </aside>

            <!-- Main Content -->
            <main class="main-content">
                <div class="content-container">
                    <!-- Dashboard Page -->
                    <div id="dashboard-page" class="page active">
                        <div class="page-header">
                            <h2>Dashboard</h2>
                            <p>Welcome to your application dashboard</p>
                        </div>
                        
                        <div class="dashboard-grid">
                            <div class="dashboard-card">
                                <div class="card-header">
                                    <h3>Total Sales</h3>
                                    <i class="fas fa-dollar-sign card-icon"></i>
                                </div>
                                <div class="card-content">
                                    <div class="metric-value">$24,500</div>
                                    <div class="metric-change positive">+12.5%</div>
                                </div>
                            </div>
                            
                            <div class="dashboard-card">
                                <div class="card-header">
                                    <h3>New Orders</h3>
                                    <i class="fas fa-shopping-bag card-icon"></i>
                                </div>
                                <div class="card-content">
                                    <div class="metric-value">156</div>
                                    <div class="metric-change positive">+8.2%</div>
                                </div>
                            </div>
                            
                            <div class="dashboard-card">
                                <div class="card-header">
                                    <h3>Active Users</h3>
                                    <i class="fas fa-users card-icon"></i>
                                </div>
                                <div class="card-content">
                                    <div class="metric-value">1,234</div>
                                    <div class="metric-change negative">-2.1%</div>
                                </div>
                            </div>
                            
                            <div class="dashboard-card">
                                <div class="card-header">
                                    <h3>Conversion Rate</h3>
                                    <i class="fas fa-chart-pie card-icon"></i>
                                </div>
                                <div class="card-content">
                                    <div class="metric-value">3.2%</div>
                                    <div class="metric-change positive">+0.5%</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="chart-container">
                            <h3>Sales Overview</h3>
                            <div class="chart-placeholder">
                                <i class="fas fa-chart-area"></i>
                                <p>Chart would be displayed here</p>
                            </div>
                        </div>
                    </div>

                    <!-- Other Pages (Hidden by default) -->
                    <div id="products-page" class="page">
                        <div class="page-header">
                            <h2>Products</h2>
                            <button class="btn btn-primary">Add Product</button>
                        </div>
                        <div class="data-table">
                            <p>Product management interface would be here</p>
                        </div>
                    </div>

                    <div id="orders-page" class="page">
                        <div class="page-header">
                            <h2>Orders</h2>
                            <button class="btn btn-primary">New Order</button>
                        </div>
                        <div class="data-table">
                            <p>Order management interface would be here</p>
                        </div>
                    </div>

                    <!-- Loading State -->
                    <div id="loading" class="loading-container" style="display: none;">
                        <div class="loading-spinner"></div>
                        <p>Loading...</p>
                    </div>
                </div>
            </main>
        </div>

        <!-- Sidebar Overlay -->
        <div class="sidebar-overlay" id="sidebarOverlay"></div>
    </div>

    <script src="script.js"></script>
</body>
</html>
'''
        
        files["styles.css"] = '''/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
        'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
        sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: #f8f9fa;
    color: #333;
    line-height: 1.6;
}

/* App Layout */
.app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.app-layout {
    display: flex;
    flex: 1;
    overflow: hidden;
}

/* Header Styles */
.header {
    background: #ffffff;
    border-bottom: 1px solid #e9ecef;
    padding: 0 20px;
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    z-index: 1000;
    position: relative;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 16px;
}

.menu-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px;
    border-radius: 6px;
    color: #6c757d;
    font-size: 18px;
    transition: all 0.2s ease;
}

.menu-button:hover {
    background-color: #f8f9fa;
    color: #333;
}

.header-title {
    font-size: 24px;
    font-weight: 600;
    color: #333;
    margin: 0;
}

.header-nav {
    display: flex;
    align-items: center;
    gap: 12px;
}

.nav-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 8px 12px;
    border-radius: 6px;
    color: #6c757d;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s ease;
}

.nav-button:hover {
    background-color: #f8f9fa;
    color: #333;
}

.user-button {
    display: flex;
    align-items: center;
    gap: 8px;
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 20px;
    transition: all 0.2s ease;
}

.user-button:hover {
    background-color: #f8f9fa;
}

.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 14px;
}

/* Sidebar Styles */
.sidebar-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 998;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
}

.sidebar-overlay.active {
    opacity: 1;
    visibility: visible;
}

.sidebar {
    position: fixed;
    top: 0;
    left: -280px;
    width: 280px;
    height: 100vh;
    background: #ffffff;
    border-right: 1px solid #e9ecef;
    transition: left 0.3s ease;
    z-index: 999;
    display: flex;
    flex-direction: column;
    box-shadow: 2px 0 8px rgba(0,0,0,0.1);
}

.sidebar.open {
    left: 0;
}

.sidebar-header {
    padding: 20px;
    border-bottom: 1px solid #e9ecef;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.sidebar-header h2 {
    font-size: 18px;
    font-weight: 600;
    color: #333;
}

.close-button {
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #6c757d;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s ease;
}

.close-button:hover {
    background-color: #f8f9fa;
    color: #333;
}

.sidebar-nav {
    flex: 1;
    padding: 16px 0;
    overflow-y: auto;
}

.nav-list {
    list-style: none;
}

.nav-item {
    margin-bottom: 4px;
}

.nav-link {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px;
    color: #6c757d;
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.2s ease;
    border-radius: 0;
}

.nav-link:hover {
    background-color: #f8f9fa;
    color: #333;
}

.nav-link.active {
    background-color: #e3f2fd;
    color: #1976d2;
    border-right: 3px solid #1976d2;
}

.nav-icon {
    font-size: 16px;
    width: 20px;
    text-align: center;
}

.sidebar-footer {
    padding: 16px 20px;
    border-top: 1px solid #e9ecef;
}

.logout-button {
    display: flex;
    align-items: center;
    gap: 12px;
    background: none;
    border: none;
    width: 100%;
    padding: 12px 0;
    color: #dc3545;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.logout-button:hover {
    color: #c82333;
}

/* Main Content Styles */
.main-content {
    flex: 1;
    overflow-y: auto;
    background-color: #f8f9fa;
}

.content-container {
    padding: 24px;
    max-width: 1200px;
    margin: 0 auto;
}

/* Page Styles */
.page {
    display: none;
}

.page.active {
    display: block;
}

.page-header {
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.page-header h2 {
    font-size: 28px;
    font-weight: 600;
    color: #333;
    margin: 0;
}

.page-header p {
    color: #6c757d;
    margin: 4px 0 0 0;
}

/* Button Styles */
.btn {
    padding: 10px 20px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    text-decoration: none;
}

.btn-primary {
    background-color: #007bff;
    color: white;
}

.btn-primary:hover {
    background-color: #0056b3;
    transform: translateY(-1px);
}

/* Dashboard Styles */
.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px;
    margin-bottom: 32px;
}

.dashboard-card {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: all 0.2s ease;
}

.dashboard-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}

.card-header h3 {
    font-size: 16px;
    font-weight: 500;
    color: #6c757d;
    margin: 0;
}

.card-icon {
    font-size: 24px;
    color: #007bff;
}

.card-content {
    display: flex;
    align-items: baseline;
    gap: 12px;
}

.metric-value {
    font-size: 32px;
    font-weight: 700;
    color: #333;
}

.metric-change {
    font-size: 14px;
    font-weight: 500;
    padding: 4px 8px;
    border-radius: 16px;
}

.metric-change.positive {
    color: #28a745;
    background-color: #d4edda;
}

.metric-change.negative {
    color: #dc3545;
    background-color: #f8d7da;
}

/* Chart Container */
.chart-container {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.chart-container h3 {
    margin-bottom: 20px;
    font-size: 18px;
    font-weight: 600;
    color: #333;
}

.chart-placeholder {
    height: 300px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background-color: #f8f9fa;
    border-radius: 8px;
    color: #6c757d;
}

.chart-placeholder i {
    font-size: 48px;
    margin-bottom: 16px;
}

/* Loading Styles */
.loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    gap: 20px;
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

/* Data Table */
.data-table {
    background: white;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    min-height: 400px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #6c757d;
}

/* Responsive Design */
@media (min-width: 1024px) {
    .sidebar {
        position: static;
        left: 0;
        width: 260px;
        box-shadow: none;
    }
    
    .sidebar-overlay {
        display: none;
    }
    
    .close-button {
        display: none;
    }
    
    .main-content {
        margin-left: 0;
    }
}

@media (max-width: 768px) {
    .header-title {
        font-size: 20px;
    }
    
    .content-container {
        padding: 16px;
    }
    
    .dashboard-grid {
        grid-template-columns: 1fr;
        gap: 16px;
    }
    
    .page-header {
        flex-direction: column;
        align-items: flex-start;
    }
    
    .nav-button span {
        display: none;
    }
}

@media (max-width: 480px) {
    .header {
        padding: 0 16px;
    }
    
    .dashboard-card {
        padding: 20px;
    }
    
    .metric-value {
        font-size: 28px;
    }
}
'''
        
        files["script.js"] = '''// Application JavaScript
class AppManager {
    constructor() {
        this.currentPage = 'dashboard';
        this.sidebarOpen = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateActiveNavLink();
        this.checkResponsive();
        
        // Initialize with sample data
        this.loadSampleData();
        
        window.addEventListener('resize', () => this.checkResponsive());
    }

    bindEvents() {
        // Menu toggle
        const menuToggle = document.getElementById('menuToggle');
        const sidebarClose = document.getElementById('sidebarClose');
        const sidebarOverlay = document.getElementById('sidebarOverlay');

        if (menuToggle) {
            menuToggle.addEventListener('click', () => this.toggleSidebar());
        }

        if (sidebarClose) {
            sidebarClose.addEventListener('click', () => this.closeSidebar());
        }

        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => this.closeSidebar());
        }

        // Navigation links
        const navLinks = document.querySelectorAll('.nav-link[data-page]');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.currentTarget.getAttribute('data-page');
                this.navigateToPage(page);
            });
        });

        // Button interactions
        this.bindButtonEvents();
    }

    bindButtonEvents() {
        // Add Product button
        const addProductBtn = document.querySelector('#products-page .btn-primary');
        if (addProductBtn) {
            addProductBtn.addEventListener('click', () => {
                this.showNotification('Add Product feature would be implemented here', 'info');
            });
        }

        // New Order button
        const newOrderBtn = document.querySelector('#orders-page .btn-primary');
        if (newOrderBtn) {
            newOrderBtn.addEventListener('click', () => {
                this.showNotification('New Order feature would be implemented here', 'info');
            });
        }

        // Notification and Settings buttons
        const notificationBtn = document.querySelector('.nav-button');
        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => {
                this.showNotification('Notifications panel would open here', 'info');
            });
        }
    }

    toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
        this.updateSidebarState();
    }

    closeSidebar() {
        this.sidebarOpen = false;
        this.updateSidebarState();
    }

    updateSidebarState() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');

        if (sidebar) {
            sidebar.classList.toggle('open', this.sidebarOpen);
        }

        if (overlay) {
            overlay.classList.toggle('active', this.sidebarOpen);
        }
    }

    navigateToPage(page) {
        // Hide all pages
        const pages = document.querySelectorAll('.page');
        pages.forEach(p => p.classList.remove('active'));

        // Show target page
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.classList.add('active');
            this.currentPage = page;
        }

        // Update navigation
        this.updateActiveNavLink();
        
        // Close sidebar on mobile
        if (window.innerWidth < 1024) {
            this.closeSidebar();
        }

        // Load page-specific data
        this.loadPageData(page);
    }

    updateActiveNavLink() {
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-page') === this.currentPage) {
                link.classList.add('active');
            }
        });
    }

    checkResponsive() {
        const isDesktop = window.innerWidth >= 1024;
        
        if (isDesktop) {
            this.sidebarOpen = true;
        } else {
            this.sidebarOpen = false;
        }
        
        this.updateSidebarState();
    }

    loadPageData(page) {
        // Simulate loading different data for different pages
        this.showLoading(true);
        
        setTimeout(() => {
            this.showLoading(false);
            
            switch (page) {
                case 'products':
                    this.loadProductsData();
                    break;
                case 'orders':
                    this.loadOrdersData();
                    break;
                case 'customers':
                    this.loadCustomersData();
                    break;
                case 'analytics':
                    this.loadAnalyticsData();
                    break;
                default:
                    break;
            }
        }, 800);
    }

    loadSampleData() {
        // Update dashboard metrics with sample data
        this.updateDashboardMetrics();
    }

    updateDashboardMetrics() {
        // This would typically fetch real data from an API
        const metrics = {
            sales: '$24,500',
            orders: '156',
            users: '1,234',
            conversion: '3.2%'
        };

        // Update UI elements would go here
        console.log('Dashboard metrics updated:', metrics);
    }

    loadProductsData() {
        console.log('Loading products data...');
        this.showNotification('Products data loaded', 'success');
    }

    loadOrdersData() {
        console.log('Loading orders data...');
        this.showNotification('Orders data loaded', 'success');
    }

    loadCustomersData() {
        console.log('Loading customers data...');
        this.showNotification('Customers data loaded', 'success');
    }

    loadAnalyticsData() {
        console.log('Loading analytics data...');
        this.showNotification('Analytics data loaded', 'success');
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '6px',
            color: 'white',
            fontWeight: '500',
            zIndex: '9999',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease'
        });

        // Set background color based on type
        const colors = {
            success: '#28a745',
            error: '#dc3545',
            warning: '#ffc107',
            info: '#17a2b8'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        // Add to document
        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Remove after delay
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // API simulation methods
    async fetchData(endpoint) {
        // Simulate API call
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    data: `Sample data from ${endpoint}`,
                    status: 'success'
                });
            }, Math.random() * 1000 + 500);
        });
    }

    async saveData(endpoint, data) {
        // Simulate API call
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    message: `Data saved to ${endpoint}`,
                    status: 'success'
                });
            }, Math.random() * 1000 + 500);
        });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.appManager = new AppManager();
    console.log('Application initialized successfully');
});

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppManager;
}
'''
        
        return files
    
    def generate_ui_from_handoff(self, handoff_content: str, context: Dict[str, Any]) -> Dict[str, str]:
        """Generate UI components based on handoff from another agent"""
        files = {}
        
        # Parse handoff content to determine UI requirements
        if "react" in handoff_content.lower():
            files.update(self.generate_react_components(handoff_content))
        elif "vue" in handoff_content.lower():
            files.update(self.generate_vue_components(handoff_content))
        else:
            files.update(self.generate_html_css_components(handoff_content))
        
        return files
    
    def get_system_prompt(self) -> str:
        """Get specialized system prompt for UI designer"""
        base_prompt = super().get_system_prompt()
        return base_prompt + """
        
        As the UI Designer agent, you:
        - Create intuitive and accessible user interfaces
        - Design responsive layouts that work across devices
        - Generate clean, semantic HTML and efficient CSS
        - Implement modern UI patterns and best practices
        - Create reusable component architectures
        - Focus on user experience and visual hierarchy
        
        When designing interfaces:
        1. Prioritize user experience and accessibility
        2. Create responsive designs that work on all devices
        3. Use semantic HTML and clean CSS structure
        4. Implement modern design patterns and components
        5. Ensure consistent visual language and branding
        6. Generate complete, functional UI code
        
        Hand off to:
        - code_generator: For backend integration and API connections
        - test_writer: For UI testing and accessibility validation
        - debugger: If UI issues or bugs are detected
        """
