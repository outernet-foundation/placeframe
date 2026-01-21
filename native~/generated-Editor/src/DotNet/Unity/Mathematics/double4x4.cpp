#include <DotNet/Unity/Mathematics/double4x4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/double4.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct double4x4;
}
namespace DotNet::Unity::Mathematics {
struct double4;
}

namespace DotNet::Unity::Mathematics {

void (*double4x4::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


double4x4 double4x4::Construct()
{
    void* reinteropException = nullptr;
    double4x4 result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*double4x4::Construct_Y_Piywi9K91QLK9aeVlq1w)(const ::DotNet::Unity::Mathematics::double4* c0, const ::DotNet::Unity::Mathematics::double4* c1, const ::DotNet::Unity::Mathematics::double4* c2, const ::DotNet::Unity::Mathematics::double4* c3, ::DotNet::Unity::Mathematics::double4x4* pReturnValue, void** reinteropException) = nullptr;


double4x4 double4x4::Construct(const ::DotNet::Unity::Mathematics::double4& c0, const ::DotNet::Unity::Mathematics::double4& c1, const ::DotNet::Unity::Mathematics::double4& c2, const ::DotNet::Unity::Mathematics::double4& c3)
{
    void* reinteropException = nullptr;
    double4x4 result;
    Construct_Y_Piywi9K91QLK9aeVlq1w(&c0, &c1, &c2, &c3, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Unity::Mathematics::double4x4::Property_get_Item)(const ::DotNet::Unity::Mathematics::double4x4* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::double4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::double4 double4x4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::double4 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


