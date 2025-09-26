/**
 * Request queue system to prevent overwhelming the backend with concurrent requests
 */

interface QueuedRequest {
  id: string;
  request: () => Promise<any>;
  resolve: (value: any) => void;
  reject: (error: any) => void;
  retries: number;
  maxRetries: number;
}

class RequestQueue {
  private queue: QueuedRequest[] = [];
  private activeRequests = 0;
  private readonly maxConcurrentRequests: number;
  private readonly defaultMaxRetries: number;
  private readonly retryDelay: number;
  private processing = false;

  constructor(
    maxConcurrentRequests: number = 3,
    defaultMaxRetries: number = 3,
    retryDelay: number = 1000
  ) {
    this.maxConcurrentRequests = maxConcurrentRequests;
    this.defaultMaxRetries = defaultMaxRetries;
    this.retryDelay = retryDelay;
  }

  /**
   * Add a request to the queue
   */
  async enqueue<T>(
    request: () => Promise<T>,
    maxRetries: number = this.defaultMaxRetries
  ): Promise<T> {
    return new Promise((resolve, reject) => {
      const queuedRequest: QueuedRequest = {
        id: Math.random().toString(36).substr(2, 9),
        request,
        resolve,
        reject,
        retries: 0,
        maxRetries,
      };

      this.queue.push(queuedRequest);
      this.processQueue();
    });
  }

  /**
   * Process the queue
   */
  private async processQueue(): Promise<void> {
    if (this.processing) return;
    this.processing = true;

    while (this.queue.length > 0 && this.activeRequests < this.maxConcurrentRequests) {
      const queuedRequest = this.queue.shift();
      if (queuedRequest) {
        this.activeRequests++;
        this.executeRequest(queuedRequest);
      }
    }

    this.processing = false;
  }

  /**
   * Execute a single request with retry logic
   */
  private async executeRequest(queuedRequest: QueuedRequest): Promise<void> {
    try {
      const result = await queuedRequest.request();
      queuedRequest.resolve(result);
    } catch (error) {
      if (queuedRequest.retries < queuedRequest.maxRetries) {
        queuedRequest.retries++;

        // Exponential backoff delay
        const delay = this.retryDelay * Math.pow(2, queuedRequest.retries - 1);

        console.warn(
          `Request failed, retrying in ${delay}ms (attempt ${queuedRequest.retries}/${queuedRequest.maxRetries})`,
          error
        );

        setTimeout(() => {
          this.queue.unshift(queuedRequest); // Put back at front of queue
          this.processQueue();
        }, delay);
      } else {
        console.error('Request failed after maximum retries:', error);
        queuedRequest.reject(error);
      }
    } finally {
      this.activeRequests--;
      this.processQueue(); // Process next requests
    }
  }

  /**
   * Get queue status for monitoring
   */
  getStatus() {
    return {
      queueLength: this.queue.length,
      activeRequests: this.activeRequests,
      maxConcurrentRequests: this.maxConcurrentRequests,
    };
  }

  /**
   * Clear the queue (for testing or emergency situations)
   */
  clear() {
    this.queue.forEach(req =>
      req.reject(new Error('Request queue cleared'))
    );
    this.queue = [];
  }
}

// Global request queue instance
export const globalRequestQueue = new RequestQueue(3, 3, 1000);

/**
 * Helper function to wrap API calls with queue management
 */
export function queuedRequest<T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  return globalRequestQueue.enqueue(apiCall, maxRetries);
}