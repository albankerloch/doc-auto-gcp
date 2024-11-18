/**
 * @file user_manager.h
 * @brief Gestion des utilisateurs avec structures et typedefs.
 * 
 * Fournit des fonctions pour créer, mettre à jour et afficher les informations
 * d'un utilisateur structuré.
 * 
 * @author Nom
 * @date YYYY-MM-DD
 */

#ifndef USER_MANAGER_H
#define USER_MANAGER_H

#include <stdbool.h>

/**
 * @struct User
 * @brief Représente un utilisateur.
 * 
 * Une structure pour stocker les informations d'un utilisateur, 
 * y compris son identifiant, son nom, son âge et son état actif.
 */
typedef struct {
    int id;          /**< Identifiant unique de l'utilisateur. */
    char name[50];   /**< Nom de l'utilisateur (max 50 caractères). */
    int age;         /**< Âge de l'utilisateur. */
    bool is_active;  /**< Indique si l'utilisateur est actif. */
} User;

/**
 * @brief Crée un nouvel utilisateur.
 * 
 * Cette fonction initialise une structure `User` avec les valeurs fournies.
 * 
 * @param[in] id Identifiant unique de l'utilisateur.
 * @param[in] name Nom de l'utilisateur.
 * @param[in] age Âge de l'utilisateur.
 * @param[in] is_active Indique si l'utilisateur est actif.
 * @return Une structure `User` initialisée.
 * 
 * @code
 * User user = create_user(1, "Alice", 25, true);
 * @endcode
 */
User create_user(int id, const char* name, int age, bool is_active);

/**
 * @brief Met à jour l'état actif d'un utilisateur.
 * 
 * Modifie le champ `is_active` de la structure `User` pour refléter le nouvel état.
 * 
 * @param[in,out] user Pointeur vers l'utilisateur à modifier.
 * @param[in] is_active Le nouvel état actif.
 * 
 * @code
 * update_user_status(&user, false);
 * @endcode
 */
void update_user_status(User* user, bool is_active);

/**
 * @brief Affiche les informations d'un utilisateur.
 * 
 * Cette fonction imprime dans la console les détails d'un utilisateur, y compris 
 * son identifiant, son nom, son âge et son état actif.
 * 
 * @param[in] user Pointeur vers l'utilisateur à afficher.
 * 
 * @code
 * print_user(&user);
 * @endcode
 */
void print_user(const User* user);

#endif // USER_MANAGER_H