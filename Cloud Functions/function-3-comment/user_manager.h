#ifndef USER_MANAGER_H
#define USER_MANAGER_H

#include <stdbool.h>

typedef struct {
    int id;
    char name[50];
    int age;
    bool is_active;
} User;


User create_user(int id, const char* name, int age, bool is_active);

void update_user_status(User* user, bool is_active);

void print_user(const User* user);

#endif