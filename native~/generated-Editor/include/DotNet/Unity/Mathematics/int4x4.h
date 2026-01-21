#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Unity/Mathematics/int4.h>

namespace DotNet::Unity::Mathematics {
struct int4;
}
namespace DotNet::Unity::Mathematics {
struct int4x4;
}

namespace DotNet::Unity::Mathematics {

struct int4x4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct___u7bLaYK7NsvS7W3VaLQcw)(const ::DotNet::Unity::Mathematics::int4* c0, const ::DotNet::Unity::Mathematics::int4* c1, const ::DotNet::Unity::Mathematics::int4* c2, const ::DotNet::Unity::Mathematics::int4* c3, ::DotNet::Unity::Mathematics::int4x4* pReturnValue, void** reinteropException);
  public: static int4x4 Construct(const ::DotNet::Unity::Mathematics::int4& c0, const ::DotNet::Unity::Mathematics::int4& c1, const ::DotNet::Unity::Mathematics::int4& c2, const ::DotNet::Unity::Mathematics::int4& c3);
  public: ::DotNet::Unity::Mathematics::int4 c0;
  public: ::DotNet::Unity::Mathematics::int4 c1;
  public: ::DotNet::Unity::Mathematics::int4 c2;
  public: ::DotNet::Unity::Mathematics::int4 c3;
};

} // namespace DotNet::Unity::Mathematics


