/**
 * @file struct.c
 * @brief Gestion des structures et des mutex pour les philosophes.
 * 
 * Ce fichier contient les fonctions nécessaires pour créer, initialiser
 * et nettoyer les structures utilisées dans le programme, notamment
 * les philosophes et leurs mutex.
 */

#include "philo_one.h"

/**
 * @brief Libère la mémoire et détruit les mutex.
 * 
 * Cette fonction détruit les mutex associés à chaque philosophe et
 * libère la mémoire allouée à la structure `philo`. Elle détruit également
 * le mutex global `lock_std`.
 * 
 * @param var Pointeur vers la structure contenant les variables globales.
 * @param i Indice du premier philosophe.
 * @param l Indice du dernier philosophe (0 si c'est le dernier, sinon 1).
 * @return Toujours retourne 1 (indique que l'opération a été effectuée).
 */
int ft_clear(t_bin *var, int i, int l)
{
    int j;

    j = 1;
    while (j < i + 1)
    {
        pthread_mutex_destroy(&(var->philo[i].lock)); /**< Destruction du mutex de verrouillage. */
        if (l == 0 && j == i)
            break;
        pthread_mutex_destroy(&(var->philo[i].eat)); /**< Destruction du mutex de temps de repas. */
        j++;
    }
    pthread_mutex_destroy(&(var->lock_std)); /**< Destruction du mutex global. */
    free(var->philo); /**< Libération de la mémoire allouée aux philosophes. */
    return (1);
}

/**
 * @brief Crée et initialise les structures des philosophes.
 * 
 * Cette fonction configure les structures de chaque philosophe, lie les mutex,
 * et initialise leurs valeurs par défaut. Chaque philosophe est relié
 * à un suivant pour former une liste circulaire.
 * 
 * @param var Pointeur vers la structure contenant les variables globales.
 * @param i Indice du premier philosophe.
 * @return Retourne 0 si la création est réussie, sinon une valeur différente de 0.
 */
static int ft_create_philo(t_bin *var, int i)
{
    while (i < var->nb + 1)
    {
        if (i == var->nb)
            var->philo[i].next = &(var->philo[1]); /**< Liaison au premier philosophe (liste circulaire). */
        else
            var->philo[i].next = &(var->philo[i + 1]); /**< Liaison au philosophe suivant. */

        var->philo[i].value = i; /**< Affectation de l'identifiant du philosophe. */
        var->philo[i].tt_die = var->time_to_die; /**< Temps avant de mourir sans manger. */
        var->philo[i].tt_eat = var->time_to_eat; /**< Temps nécessaire pour manger. */
        var->philo[i].tt_sleep = var->time_to_sleep; /**< Temps nécessaire pour dormir. */
        var->philo[i].count_eat = 0; /**< Compteur initialisé à 0. */
        var->philo[i].end = 0; /**< Indicateur de fin initialisé à 0. */
        var->philo[i].nb_eat = var->nb_eat; /**< Nombre de repas nécessaires. */
        var->philo[i].str[0] = '\0'; /**< Chaîne initialisée à vide. */
        var->philo[i].var = var; /**< Pointeur vers la structure globale. */
        var->philo[i].lock_std = &(var->lock_std); /**< Pointeur vers le mutex global. */

        if (pthread_mutex_init(&(var->philo[i].lock), NULL) != 0) /**< Initialisation du mutex de verrouillage. */
            return ((!(ft_clear(var, i, 0))));
        if (pthread_mutex_init(&(var->philo[i].eat), NULL) != 0) /**< Initialisation du mutex de repas. */
            return ((!(ft_clear(var, i, 1))));
        i++;
    }
    return (0);
}

/**
 * @brief Crée et initialise les structures principales du programme.
 * 
 * Cette fonction alloue la mémoire nécessaire pour les philosophes et
 * initialise les mutex globaux ainsi que les structures individuelles.
 * 
 * @param var Pointeur vers la structure contenant les variables globales.
 * @return Retourne 0 si la création est réussie, sinon 1.
 */
int ft_create(t_bin *var)
{
    if (pthread_mutex_init(&(var->lock_std), NULL) != 0) /**< Initialisation du mutex global. */
        return (1);
    if (!(var->philo = malloc((var->nb + 1) * sizeof(t_node)))) /**< Allocation mémoire pour les philosophes. */
    {
        pthread_mutex_destroy(&(var->lock_std)); /**< Destruction du mutex global en cas d'échec. */
        return (1);
    }
    if (ft_create_philo(var, 1)) /**< Appel de la fonction pour initialiser les philosophes. */
        return (1);
    return (0);
}