#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double3;
}

namespace DotNet::Unity::Mathematics {

struct double3 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: static double3 Construct();
  private: static void (*Construct_vFScQRRHVnKCy1ZblYgxig)(double x, double y, double z, ::DotNet::Unity::Mathematics::double3* pReturnValue, void** reinteropException);
  public: static double3 Construct(double x, double y, double z);
  private: static double (*Property_get_Item)(const ::DotNet::Unity::Mathematics::double3* thiz, ::std::int32_t index, void** reinteropException);
  public: double operator[](::std::int32_t index) const;
  public: double x;
  public: double y;
  public: double z;
};

} // namespace DotNet::Unity::Mathematics


