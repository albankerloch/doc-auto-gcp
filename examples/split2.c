/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ft_split.c                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: rkhelif <rkhelif@student.42.fr>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2020/08/25 15:10:08 by rkhelif           #+#    #+#             */
/*   Updated: 2020/08/25 21:37:57 by rkhelif          ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include <stdlib.h>

/**
 * @brief Compare deux chaînes de caractères.
 * 
 * @param str La première chaîne de caractères.
 * @param charset La deuxième chaîne de caractères.
 * @param i L'index de départ de la comparaison dans charset.
 * @return Le nombre de caractères identiques si les chaînes sont identiques jusqu'à la fin de charset, 0 sinon.
 */
int		ft_strncmp(char *str, char *charset, int i)
{
	while (charset[++i])
		if (charset[i] != str[i])
			return (0);
	return (i);
}

/**
 * @brief Compte le nombre de lignes dans une chaîne de caractères, en utilisant un séparateur.
 * 
 * @param str La chaîne de caractères à analyser.
 * @param charset La chaîne de caractères séparateur.
 * @param i L'index de départ dans str.
 * @param j Un indicateur pour savoir si un séparateur a été trouvé.
 * @return Le nombre de lignes dans la chaîne de caractères.
 */
int		ft_line(char *str, char *charset, int i, int j)
{
	int	nbr;

	nbr = 0;
	while (str[i] == charset[0] && (ft_strncmp(str + i, charset, -1) > 0))
		i += ft_strncmp(str + i, charset, -1);
	nbr = (str[i] != '\0') ? nbr + 1 : nbr;
	while (str[i])
	{
		while (str[i] == charset[0] &&
		(ft_strncmp(str + i, charset, -1) > 0) && ++j != 0)
			i += ft_strncmp(str + i, charset, -1);
		(j > 0 && str[i] != '\0') ? nbr++ : 0;
		j = 0;
		i = (str[i] == '\0') ? i : i + 1;
	}
	return (nbr);
}

/**
 * @brief Alloue de la mémoire pour une ligne de la chaîne de caractères.
 * 
 * @param str La chaîne de caractères à analyser.
 * @param charset La chaîne de caractères séparateur.
 * @param tab La ligne de la chaîne de caractères.
 * @param i L'index de départ dans str.
 * @return Un pointeur vers la mémoire allouée, ou NULL en cas d'erreur.
 */
char	*ft_put_malloc(char *str, char *charset, char *tab, int i)
{
	int	k;
	int	x;

	x = 0;
	while (str[i] == charset[0] && (ft_strncmp(str + i, charset, -1) > 0))
		i += ft_strncmp(str + i, charset, -1);
	k = i;
	while (str[i] && x == 0)
	{
		if (str[i] == charset[0] && (ft_strncmp(str + i, charset, -1) > 0))
			x = 1;
		(x == 0) ? i++ : 0;
	}
	if ((tab = malloc(sizeof(charset[0]) * ((i - k) + 1))) == NULL)
		return (NULL);
	return (tab);
}

/**
 * @brief Copie une ligne de la chaîne de caractères dans la mémoire allouée.
 * 
 * @param str La chaîne de caractères à analyser.
 * @param charset La chaîne de caractères séparateur.
 * @param tab La ligne de la chaîne de caractères.
 * @param i L'index de départ dans str.
 * @return L'index de la fin de la ligne dans str.
 */
int		ft_put_in_tab(char *str, char *charset, char *tab, int i)
{
	int	k;
	int	x;

	x = 0;
	k = -1;
	while (str[i] == charset[0] && (ft_strncmp(str + i, charset, -1) > 0))
		i += ft_strncmp(str + i, charset, -1);
	while (str[i] && x == 0)
	{
		if (str[i] == charset[0] && (ft_strncmp(str + i, charset, -1) > 0))
			x = 1;
		if (x == 0)
			tab[++k] = str[i];
		(x == 0) ? i++ : 0;
	}
	tab[++k] = '\0';
	return (i);
}

/**
 * @brief Divise une chaîne de caractères en un tableau de chaînes de caractères, en utilisant un séparateur.
 * 
 * @param str La chaîne de caractères à diviser.
 * @param charset La chaîne de caractères séparateur.
 * @return Un tableau de chaînes de caractères, ou NULL en cas d'erreur.
 */
char	**ft_split(char *str, char *charset)
{
	char	**tab;
	int		nbr_line;
	int		i;
	int		j;

	j = -1;
	tab = NULL;
	i = 0;
	nbr_line = ft_line(str, charset, 0, 0);
	if ((tab = malloc(sizeof(tab[0]) * (nbr_line + 1))) == NULL)
		return (NULL);
	while (++j < nbr_line)
	{
		if ((tab[j] = ft_put_malloc(str + i, charset, tab[j], 0)) == NULL)
			return (NULL);
		i += ft_put_in_tab(str + i, charset, tab[j], 0);
	}
	tab[nbr_line] = 0;
	return (tab);
}
