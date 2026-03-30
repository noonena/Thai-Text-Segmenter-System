// Dynamic API configuration system
interface ApiEndpoint {
  protocol: string;
  host: string;
  port: number;
  base: string;
}

interface ApiServices {
  auth: ApiEndpoint;
  nlp: ApiEndpoint;
}

class ApiConfig {
  private static instance: ApiConfig;
  private services: ApiServices;
  private initialized = false;

  private constructor() {
    this.services = {
      auth: { protocol: 'http', host: 'localhost', port: 8002, base: 'api' },
      nlp: { protocol: 'http', host: 'localhost', port: 8000, base: 'api' }
    };
  }

  static getInstance(): ApiConfig {
    if (!ApiConfig.instance) {
      ApiConfig.instance = new ApiConfig();
    }
    return ApiConfig.instance;
  }

  // Initialize from environment variables or configuration
  async initialize(): Promise<void> {
    if (this.initialized) return;

    console.log('🚀 Initializing API config...');
    
    // Try auto-detection first
    await this.autoDetectServices();
    
    this.initialized = true;
    console.log('🔧 API Config initialized:', this.services);
  }

  private getFromEnv(key: string): string | null {
    return (import.meta as any)?.env?.[key] || null;
  }

  private parseEndpoint(url: string, service: keyof ApiServices): void {
    try {
      const parsed = new URL(url);
      this.services[service] = {
        protocol: parsed.protocol.replace(':', ''),
        host: parsed.hostname,
        port: parseInt(parsed.port) || (parsed.protocol === 'https:' ? 443 : 80),
        base: parsed.pathname.replace(/^\//, '').replace(/\/$/, '') || 'api'
      };
    } catch (error) {
      console.warn(`⚠️ Failed to parse ${service} endpoint:`, url, error);
    }
  }

  private async autoDetectServices(): Promise<void> {
    console.log('🔍 Starting auto-detection...');
    
    // Skip auto-detection if environment variables are set
    if (this.getFromEnv('VITE_API_BASE')) {
      console.log('✅ Using environment variables, skipping auto-detection');
      return;
    }
    
    const testUrls = [
      { service: 'auth' as const, url: 'http://localhost:8002/api' },
      { service: 'auth' as const, url: 'http://127.0.0.1:8002/api' },
      { service: 'nlp' as const, url: 'http://localhost:8000/api' },
      { service: 'nlp' as const, url: 'http://127.0.0.1:8000/api' },
    ];

    for (const { service, url } of testUrls) {
      try {
        console.log(`🔍 Testing ${service} at ${url}`);
        const response = await fetch(url, {
          method: 'HEAD',
          signal: AbortSignal.timeout(2000)
        });
        
        if (response.ok || response.status === 404) { // 404 means server is running
          console.log(`✅ Found ${service} at ${url}`);
          this.parseEndpoint(url, service);
        }
      } catch (error) {
        console.log(`❌ ${service} not available at ${url}:`, error instanceof Error ? error.message : String(error));
      }
    }
  }

  

  private buildUrl(endpoint: ApiEndpoint, path: string): string {
    const cleanPath = path.replace(/^\//, '');
    return `${endpoint.protocol}://${endpoint.host}:${endpoint.port}/${endpoint.base}/${cleanPath}`;
  }

  // Public getters
  getAuthServiceUrl(path: string = ''): string {
    return this.buildUrl(this.services.auth, path);
  }

  getNlpServiceUrl(path: string = ''): string {
    return this.buildUrl(this.services.nlp, path);
  }

  getServices(): ApiServices {
    return { ...this.services };
  }

  // Manual update methods
  updateAuthEndpoint(endpoint: Partial<ApiEndpoint>): void {
    this.services.auth = { ...this.services.auth, ...endpoint };
  }

  updateNlpEndpoint(endpoint: Partial<ApiEndpoint>): void {
    this.services.nlp = { ...this.services.nlp, ...endpoint };
  }
}

export const apiConfig = ApiConfig.getInstance();
export type { ApiEndpoint, ApiServices };