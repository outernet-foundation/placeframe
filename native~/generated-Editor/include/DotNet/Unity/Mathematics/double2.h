#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double2;
}

namespace DotNet::Unity::Mathematics {

struct double2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_8gQZlbVINFTIoHYsENgIlA)(double x, double y, ::DotNet::Unity::Mathematics::double2* pReturnValue, void** reinteropException);
  public: static double2 Construct(double x, double y);
  private: static double (*Property_get_Item)(const ::DotNet::Unity::Mathematics::double2* thiz, ::std::int32_t index, void** reinteropException);
  public: double operator[](::std::int32_t index) const;
  public: double x;
  public: double y;
};

} // namespace DotNet::Unity::Mathematics


