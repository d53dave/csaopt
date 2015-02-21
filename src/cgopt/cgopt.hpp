#ifndef CGOPT_HPP_
#define CGOPT_HPP_

template<typename E>
class SAOptimization {
	SAOptimization& operator=(const SAOptimization<E>&);
	SAOptimization(const SAOptimization<E>&);
public:
	SAOptimization() {
	}
	virtual ~SAOptimization() {
	}

	virtual void add(const E& e) {
		add(&e, 1);
	}
	virtual void add(const E e[], size_t s) = 0;

	virtual void remove(const E& e) {
		remove(&e, 1);
	}
	virtual void remove(const E e[], size_t s) = 0;

	virtual bool member(const E& e) const = 0;
	virtual size_t size() const = 0;
	virtual bool empty() const {
		return size() == 0;
	}

	virtual E min() const = 0;
	virtual E max() const = 0;

	virtual std::ostream& print(std::ostream& o) const = 0;
};

template<typename E>
inline std::ostream& operator<<(std::ostream& o, const SAOptimization<E>& c) {
	return c.print(o);
}

#endif //CGOPT_HPP_
