#ifndef CGOPT_HPP_
#define CGOPT_HPP_

#include <chrono>
#include "../spdlog/spdlog.h"

template<typename E>
class SAOptimization {
	SAOptimization& operator=(const SAOptimization<E>&);
	SAOptimization(const SAOptimization<E>&);
public:
	SAOptimization();
	virtual ~SAOptimization();

	virtual void add(const E& e) {
		add(&e, 1);
	}
	virtual void add(const E e[], size_t s) = 0;

	virtual void remove(const E& e) {
		remove(&e, 1);
	}
	virtual void remove(const E e[], size_t s) = 0;

	virtual E generate_neighbour() = 0;

	virtual double generate_neighbour() = 0;

	virtual double decrease_temp() = 0;

	OptimizationOptions getOptions() {
		return options;
	}
	void setOptions(OptimizationOptions& _options) {
		options = _options;
	}

	virtual void run() const = 0;

	virtual E min() const = 0;

	virtual std::ostream& print(std::ostream& o) const = 0;

private:
	OptimizationOptions options;
};

enum temperature_decrease_method {
	STANDARD
};

class OptimizationOptions {
	OptimizationOptions& operator=(const OptimizationOptions&);
	OptimizationOptions(const OptimizationOptions&);

public:
	size_t get_max_iter() {
		return max_iter;
	}
	void set_max_iter(size_t & _max_iter) {
		max_iter = _max_iter;
	}
	std::chrono::duration get_max_runtime() {
		return max_runtime;
	}
	void set_max_runtime(std::chrono::duration & _max_runtime) {
		max_runtime = _max_runtime;
	}

	temperature_decrease_method get_decr_method() const {
		return t_decr_method;
	}

	void set_decr_method(temperature_decrease_method decr_method) {
		t_decr_method = decr_method;
	}

private:
	size_t max_iter;
	std::chrono::duration max_runtime;
	temperature_decrease_method t_decr_method;
	double initial_temp;
};

template<typename E>
inline std::ostream& operator<<(std::ostream& o, const SAOptimization<E>& c) {
	return c.print(o);
}

#endif //CGOPT_HPP_
