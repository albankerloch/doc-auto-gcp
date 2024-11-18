/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ft_atoi.c                                          :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: akerloc- <marvin@42.fr>                    +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2019/10/07 17:31:51 by akerloc-          #+#    #+#             */
/*   Updated: 2019/10/07 17:41:11 by akerloc-         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "philo_three.h"

/**
 * @file ft_atoi.c
 * @brief Implémentation de la fonction ft_atoi.
 */

/**
 * @brief Vérifie si un caractère est un caractère d'espacement.
 * 
 * @param c Le caractère à vérifier.
 * @return 1 si le caractère est un caractère d'espacement, 0 sinon.
 */
static int	ft_isspace(char c)
{
	if (c == '\t' || c == '\n' || c == '\v' ||
	c == '\f' || c == '\r' || c == ' ')
		return (1);
	else
		return (0);
}

/**
 * @brief Convertit une chaîne de caractères en entier.
 * 
 * @param str La chaîne de caractères à convertir.
 * @return L'entier converti.
 */
int			ft_atoi(const char *str)
{
	int		i;
	long	res;
	int		sign;

	i = 0;
	res = 0;
	sign = 1;
	while (ft_isspace(str[i]))
		i++;
	if (str[i] == '+' || str[i] == '-')
	{
		if (str[i] == '-')
			sign = sign * (-1);
		i++;
	}
	while (str[i] > 47 && str[i] < 58 && str[i] != '\0')
	{
		res = res * 10 + str[i] - 48;
		i++;
	}
	return (res * sign);
}