# Thai Text Segmenter - Dynamic API Configuration Guide

## Overview
This system replaces hardcoded API URLs with a dynamic, auto-detecting configuration that can work across different environments without code changes.

## How It Works

### 1. **Auto-Detection**
- Scans common ports (8000-8003, 5000, 3001) for running services
- Tests endpoints to identify auth vs NLP services
- Falls back to default URLs if auto-detection fails

### 2. **Environment Variables**
Create `.env` file in frontend root:
```bash
VITE_AUTH_API=http://localhost:8002/api
VITE_NLP_API=http://localhost:8000/api
VITE_API_TIMEOUT=10000
VITE_API_RETRIES=3
```

### 3. **Production URLs**
```bash
VITE_AUTH_API=https://api.yourdomain.com/auth/api
VITE_NLP_API=https://api.yourdomain.com/nlp/api
```

## Features

### ✅ **Dynamic Service Discovery**
- Automatically finds backend services on different ports
- No need to hardcode URLs in components
- Handles service restarts and port changes

### ✅ **Centralized Error Handling**
- Automatic retries with exponential backoff
- Timeout management
- Consistent error responses

### ✅ **Authentication Management**
- Automatic token handling
- Secure storage management
- Logout cleanup

### ✅ **Environment Support**
- Development: Auto-detection + environment files
- Production: Environment variable configuration
- Testing: Mock API responses

## Usage Examples

### **Before (Hardcoded)**
```typescript
// ❌ Hardcoded, brittle
const API_BASE = 'http://localhost:8002/api';
const response = await fetch(`${API_BASE}/users`);
```

### **After (Dynamic)**
```typescript
// ✅ Dynamic, resilient
import { apiClient } from '../services/api';

const response = await apiClient.getUsers();
// Auto-detects service, handles auth, retries, timeouts
```

## File Structure

```
frontend/src/
├── config/
│   └── api.ts           # Dynamic configuration logic
├── services/
│   └── api.ts           # Centralized API client
└── contexts/
    └── AuthContext.tsx  # Updated to use API client
```

## Migration Benefits

### **Developer Experience**
- No more hardcoded URLs
- Easy switching between environments
- Better error messages and debugging

### **Operations**
- Deploy to any environment without code changes
- Handle service migrations seamlessly
- Monitor API performance centrally

### **Maintainability**
- Single source of truth for API configuration
- Consistent error handling across all components
- Easy to add new API methods

## Setup Instructions

1. **Install**: The API system is already integrated
2. **Configure**: Copy `.env.example` to `.env` and adjust as needed
3. **Deploy**: Set environment variables in production
4. **Monitor**: Check console for auto-detection status

## Troubleshooting

### **Services Not Found**
```bash
# Check what's running
netstat -ano | findstr :800
netstat -ano | findstr :802
```

### **Environment Variables Not Loading**
- Ensure `.env` file is in frontend root
- Variables must start with `VITE_` for Vite
- Restart dev server after changing `.env`

### **API Timeouts**
- Increase `VITE_API_TIMEOUT` if services are slow
- Check service health with `apiClient.checkAuthHealth()`

This system makes your frontend more robust and easier to deploy across different environments!