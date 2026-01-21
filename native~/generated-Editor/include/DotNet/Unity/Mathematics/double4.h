#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double4;
}

namespace DotNet::Unity::Mathematics {

struct double4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_vGP51u8UcgYZVrSmxERqcw)(double x, double y, double z, double w, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException);
  public: static double4 Construct(double x, double y, double z, double w);
  private: static double (*Property_get_Item)(const ::DotNet::Unity::Mathematics::double4* thiz, ::std::int32_t index, void** reinteropException);
  public: double operator[](::std::int32_t index) const;
  public: double x;
  public: double y;
  public: double z;
  public: double w;
};

} // namespace DotNet::Unity::Mathematics


