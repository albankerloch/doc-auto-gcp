#include "philo_one.h"

int			ft_clear(t_bin *var, int i, int l)
{
	int j;

	j = 1;
	while (j < i + 1)
	{
		pthread_mutex_destroy(&(var->philo[i].lock));
		if (l == 0 && j == i)
			break ;
		pthread_mutex_destroy(&(var->philo[i].eat));
		j++;
	}
	pthread_mutex_destroy(&(var->lock_std));
	free(var->philo);
	return (1);
}

static int	ft_create_philo(t_bin *var, int i)
{
	while (i < var->nb + 1)
	{
		if (i == var->nb)
			var->philo[i].next = &(var->philo[1]);
		else
			var->philo[i].next = &(var->philo[i + 1]);
		var->philo[i].value = i;
		var->philo[i].tt_die = var->time_to_die;
		var->philo[i].tt_eat = var->time_to_eat;
		var->philo[i].tt_sleep = var->time_to_sleep;
		var->philo[i].count_eat = 0;
		var->philo[i].end = 0;
		var->philo[i].nb_eat = var->nb_eat;
		var->philo[i].str[0] = '\0';
		var->philo[i].var = var;
		var->philo[i].lock_std = &(var->lock_std);
		if (pthread_mutex_init(&(var->philo[i].lock), NULL) != 0)
			return ((!(ft_clear(var, i, 0))));
		if (pthread_mutex_init(&(var->philo[i].eat), NULL) != 0)
			return ((!(ft_clear(var, i, 1))));
		i++;
	}
	return (0);
}

int			ft_create(t_bin *var)
{
	if (pthread_mutex_init(&(var->lock_std), NULL) != 0)
		return (1);
	if (!(var->philo = malloc((var->nb + 1) * sizeof(t_node))))
	{
		pthread_mutex_destroy(&(var->lock_std));
		return (1);
	}
	if (ft_create_philo(var, 1))
		return (1);
	return (0);
}