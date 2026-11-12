/* PAX transaction ABI census. Documentation/public headers and the project's
 * disk probe conventions only. Run in a new private directory on a throwaway
 * QEMU root, never a host root. Success means ABI behavior, not durability. */
#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/syscall.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

static int failures;
static void row(const char *name, long got, long expected) {
    printf("%s abi-%s got=%ld want=%ld\n", got == expected ? "PASS" : "FAIL", name, got, expected);
    fflush(stdout);
    if (got != expected) failures++;
}
static long result(long r) { return r < 0 ? -errno : r; }
static void available(const char *name, int fd) {
    row(name, fd >= 0 ? 0 : -errno, 0);
    if (fd < 0) exit(2);
}
static void print_file(const char *path) {
    char b[4096];
    int fd = open(path, O_RDONLY | O_NOFOLLOW);
    printf("OBSERVE %s open=%ld\n", path, fd < 0 ? (long)-errno : 0L);
    if (fd < 0) return;
    ssize_t n;
    while ((n = read(fd, b, sizeof b)) > 0) fwrite(b, 1, (size_t)n, stdout);
    printf("\nEND-OBSERVE %s\n", path);
    close(fd);
}
int main(int argc, char **argv) {
    if (argc != 2 || argv[1][0] != '/') return 2;
    print_file("/proc/self/mounts");
    print_file("/proc/self/mountinfo");
    print_file("/etc/pax-release");
    struct statfs sf;
    long s = result(statfs("/", &sf));
    printf("OBSERVE statfs-root result=%ld", s);
    if (s == 0) printf(" type=%lx blocks=%lu free=%lu inodes=%lu ifree=%lu flags=%lx", (long)sf.f_type,
       (unsigned long)sf.f_blocks, (unsigned long)sf.f_bavail, (unsigned long)sf.f_files,
       (unsigned long)sf.f_ffree, (long)sf.f_flags);
    puts("");
    int j = open("/proc/fs/jbd2", O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    printf("OBSERVE linux-journal-signal=%ld\n", j < 0 ? (long)-errno : 0L);
    if (j >= 0) close(j);
    long made = result(mkdir(argv[1], 0700));
    row("private-directory", made, 0);
    if (made != 0) return 2;
    int d = open(argv[1], O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    available("open-directory-nofollow", d);
    row("statfs-directory", result(fstatfs(d, &sf)), 0);
    row("mkdirat", result(mkdirat(d, "parent", 0700)), 0);
    int p = openat(d, "parent", O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    available("openat-parent-nofollow", p);
    int f = openat(p, "file", O_RDWR | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    available("openat-create-exclusive-nofollow", f);
    int x = openat(p, "file", O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    row("exclusive-existing", x < 0 ? -errno : 0, -EEXIST);
    if (x >= 0) close(x);
    row("write", result(write(f, "old\n", 4)), 4);
    row("fchmod", result(fchmod(f, 0640)), 0);
    row("fchown", result(fchown(f, 0, 0)), 0);
    row("fsync-file", result(fsync(f)), 0);
    row("fdatasync-file", result(fdatasync(f)), 0);
    row("fsync-directory", result(fsync(p)), 0);
    struct stat before = {0}, after = {0};
    row("fstat", result(fstat(f, &before)), 0);
    row("renameat", result(renameat(p, "file", p, "renamed")), 0);
    row("newfstatat", result(fstatat(p, "renamed", &after, AT_SYMLINK_NOFOLLOW)), 0);
    row("rename-preserves-inode", before.st_dev == after.st_dev && before.st_ino == after.st_ino, 1);
    row("symlinkat", result(symlinkat("parent", d, "alias")), 0);
    x = openat(d, "alias", O_RDONLY | O_DIRECTORY | O_NOFOLLOW);
    row("nofollow-symlink-ancestor", x < 0 ? -errno : 0, -ENOTDIR);
    if (x >= 0) close(x);
    row("symlink-file", result(symlinkat("renamed", p, "sym")), 0);
    x = openat(p, "sym", O_RDONLY | O_NOFOLLOW);
    row("nofollow-final-symlink", x < 0 ? -errno : 0, -ELOOP);
    if (x >= 0) close(x);
    row("fchownat-nofollow", result(fchownat(p, "sym", 123, 456, AT_SYMLINK_NOFOLLOW)), 0);
    row("lstat-symlink", result(fstatat(p, "sym", &after, AT_SYMLINK_NOFOLLOW)), 0);
    row("symlink-owner-applied", after.st_uid == 123 && after.st_gid == 456 && S_ISLNK(after.st_mode), 1);
    row("link-target-owner-unchanged", result(fstat(f, &after)), 0);
    row("target-owner-retained", after.st_uid == 0 && after.st_gid == 0, 1);
    char target[64] = {0};
    row("readlinkat", result(readlinkat(p, "sym", target, sizeof target)), 7);
    row("readlinkat-target", !memcmp(target, "renamed", 7), 1);
    row("linkat", result(linkat(p, "renamed", p, "hard", 0)), 0);
    row("hardlink-stat", result(fstatat(p, "hard", &after, AT_SYMLINK_NOFOLLOW)), 0);
    row("hardlink-identity", before.st_dev == after.st_dev && before.st_ino == after.st_ino && after.st_nlink == 2, 1);
    int replacement = openat(p, "replacement", O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    available("replacement-create", replacement);
    row("replacement-write", result(write(replacement, "new\n", 4)), 4);
    row("replacement-sync", result(fsync(replacement)), 0);
    row("rename-over-existing", result(renameat(p, "replacement", p, "renamed")), 0);
    row("rename-parent-sync", result(fsync(p)), 0);
    char data[4];
    row("old-handle-seek", result(lseek(f, 0, SEEK_SET)), 0);
    row("old-handle-read", result(read(f, data, 4)), 4);
    row("old-open-inode-retained", !memcmp(data, "old\n", 4), 1);
    close(replacement);
    int lock = openat(p, "lock", O_RDONLY | O_CREAT | O_EXCL | O_NOFOLLOW, 0600);
    available("lock-create-readonly", lock);
    row("flock-exclusive-nonblocking", result(flock(lock, LOCK_EX | LOCK_NB)), 0);
    int contender = openat(p, "lock", O_RDONLY | O_NOFOLLOW);
    available("lock-second-open", contender);
    row("flock-contention", result(flock(contender, LOCK_EX | LOCK_NB)), -EWOULDBLOCK);
    close(lock);
    row("flock-last-close-releases", result(flock(contender, LOCK_EX | LOCK_NB)), 0);
    close(contender);
    int gate[2];
    if (pipe(gate) < 0) return 2;
    pid_t child = fork();
    if (child < 0) return 2;
    if (child == 0) {
        close(gate[0]);
        int owner = openat(p, "lock", O_RDONLY | O_NOFOLLOW);
        char c = (owner >= 0 && flock(owner, LOCK_EX | LOCK_NB) == 0) ? 'y' : 'n';
        if (write(gate[1], &c, 1) != 1) _exit(2);
        _exit(c == 'y' ? 0 : 1);
    }
    close(gate[1]);
    char c = 0;
    row("flock-owner-ready", result(read(gate[0], &c, 1)), 1);
    row("flock-owner-acquired", c == 'y', 1);
    close(gate[0]);
    int status;
    row("wait-owner", waitpid(child, &status, 0) == child && WIFEXITED(status) && WEXITSTATUS(status) == 0, 1);
    contender = openat(p, "lock", O_RDONLY | O_NOFOLLOW);
    available("lock-after-owner-exit-open", contender);
    row("flock-owner-exit-releases", result(flock(contender, LOCK_EX | LOCK_NB)), 0);
    close(contender);
    char entries[4096];
    long n = syscall(SYS_getdents64, p, entries, sizeof entries);
    row("getdents64", n > 0 ? 0 : result(n), 0);
    row("fchdir", result(fchdir(p)), 0);
    row("cwd-pinned-lstat", result(lstat("renamed", &after)), 0);
    row("cwd-pinned-rename", result(rename("renamed", "final")), 0);
    row("cwd-pinned-directory-sync", result(fsync(p)), 0);
    row("unlinkat", result(unlinkat(p, "sym", 0)), 0);
    row("unlinkat-hard", result(unlinkat(p, "hard", 0)), 0);
    row("unlinkat-file", result(unlinkat(p, "final", 0)), 0);
    row("unlinkat-lock", result(unlinkat(p, "lock", 0)), 0);
    close(f);
    close(p);
    row("chdir-root", result(chdir("/")), 0);
    row("unlinkat-directory", result(unlinkat(d, "parent", AT_REMOVEDIR)), 0);
    row("unlinkat-alias", result(unlinkat(d, "alias", 0)), 0);
    row("cleanup-directory-sync", result(fsync(d)), 0);
    close(d);
    row("rmdir", result(rmdir(argv[1])), 0);
    printf("ABI-END failures=%d\n", failures);
    return failures ? 1 : 0;
}
